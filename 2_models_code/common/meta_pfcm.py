"""Common DP -> optimize [centers,a,b,w,eta] -> final PFCM pipeline."""
import numpy as np
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from common.density_peak import density_peak_centers
from common.numerics import pfcm_step, final_state, squared_distance, solve_pfcm, memberships

# Internal cluster-validity fitness. These read the hard partition, not the
# fuzzy objective, so a chromosome cannot lower its score by moving w or by
# rescaling a, b, eta. Candidate set follows the ranking reported by the
# GECCO 2021 survey of CVIs as fitness (doi 10.1145/3449639.3459341).
# Every variant is a LOSS to minimise; a degenerate partition gets a penalty.
CVI_PENALTY = 1e6

def repair_collapsed(X, centers, d2, k):
    """Move unused centres onto the worst-served points (empty-cluster repair).

    A PFCM step can leave a centre with no nearest point, so the hard partition
    has fewer than k clusters. The fuzzy objective REWARDS that (fewer, tighter
    clusters cost less), which is why a large fuzzifier merges clusters. This
    puts each unused centre on the point currently farthest from its own
    nearest centre, the standard farthest-point repair.
    """
    labels = d2.argmin(axis=1)
    used = np.unique(labels)
    missing = np.setdiff1d(np.arange(k), used)
    if not len(missing):
        return centers, False
    centers = centers.copy()
    nearest = d2.min(axis=1).copy()
    for j in missing:
        far = int(nearest.argmax())
        centers[j] = X[far]
        nearest[far] = -np.inf  # do not reuse the same point twice
    return centers, True


def cvi_loss(X, labels, kind):
    if len(np.unique(labels)) < 2:
        # One surviving cluster: no validity index is defined. Penalise rather
        # than crash, so the search can move away instead of stopping.
        return CVI_PENALTY
    if kind == "ch":
        return -float(calinski_harabasz_score(X, labels))
    if kind == "db":
        return float(davies_bouldin_score(X, labels))
    if kind == "silhouette":
        return -float(silhouette_score(X, labels))
    raise ValueError(f"Unknown CVI: {kind}")

class PFCMSearch:
    """No class labels, ARI, NMI or accuracy are available to the search."""
    def __init__(self, X, k, cfg):
        self.X, self.k, self.cfg = X, k, cfg
        self.d = X.shape[1]
        bounds = cfg["parameter_bounds"]
        self.low = np.r_[np.tile(X.min(axis=0), k), [bounds[q][0] for q in ("a","b","w","eta")]]
        self.high = np.r_[np.tile(X.max(axis=0), k), [bounds[q][1] for q in ("a","b","w","eta")]]
        self.evaluations = 0

        # GPU acceleration detection
        self.device = cfg.get("device", "auto")
        self.use_gpu = False
        # The batched GPU kernel only implements the fuzzy objectives; CVI
        # fitness must stay on the CPU path or the two would disagree silently.
        gpu_ok = cfg.get("use_gpu", True) and cfg["fitness"] not in ("ch", "db", "silhouette")
        if self.device in ("cuda", "gpu", "auto") and gpu_ok:
            try:
                from common.gpu_evaluator import is_gpu_supported, GPUBatchedPFCM
                if is_gpu_supported():
                    self.gpu_evaluator = GPUBatchedPFCM(X, k, cfg)
                    self.use_gpu = True
            except Exception:
                self.use_gpu = False

    def decode(self, gene):
        centers = gene[:self.k*self.d].reshape(self.k, self.d)
        params = dict(zip(("a", "b", "w", "eta"), map(float, gene[-4:])))
        params["gamma_scale"] = self.cfg["gamma_scale"]
        return centers, params

    def repair(self, genes):
        return np.clip(genes, self.low, self.high)

    def initial(self, anchors, rng, candidates=None):
        size = self.cfg["population"]
        genes = rng.uniform(self.low, self.high, (size, len(self.low)))
        centers = anchors[None, :, :] + rng.normal(
            0, self.cfg["seed_jitter"], (size, self.k, self.d))
        mode = self.cfg.get("init_mode", "jitter")
        if mode not in ("jitter", "diverse"):
            raise ValueError("init_mode: jitter or diverse.")
        if mode == "diverse" and candidates is not None and len(candidates) > self.k:
            # Draw each individual's k peaks from the ranked rho*delta pool, so
            # the population spans several candidate peak sets instead of one.
            pool = np.asarray(candidates)
            for p in range(1, size):
                pick = rng.choice(len(pool), size=self.k, replace=False)
                centers[p] = self.X[pool[pick]] + rng.normal(
                    0, self.cfg["seed_jitter"], (self.k, self.d))
        centers[0] = anchors
        genes[:, :self.k*self.d] = centers.reshape(size, -1)
        # First chromosome also contains the baseline parameter values.
        genes[0, -4:] = [self.cfg[q] for q in ("a", "b", "w", "eta")]
        return self.repair(genes)

    def evaluate(self, genes):
        if self.use_gpu:
            try:
                updated, scores = self.gpu_evaluator.evaluate(self.repair(genes))
                self.evaluations += len(genes)
                if not np.isfinite(scores).all():
                    raise FloatingPointError("Non-finite fitness; inspect parameter bounds.")
                return updated, scores
            except Exception:
                self.use_gpu = False  # Fallback to CPU

        scores = np.empty(len(genes))
        updated = self.repair(genes).copy()
        for i, gene in enumerate(updated):
            centers, params = self.decode(gene)
            # fitness_horizon = 1 reproduces the paper's one-step evaluation.
            # Cluster merging only emerges over many PFCM iterations, so a
            # one-step score cannot see the merging that the final refinement
            # will produce. A longer horizon scores closer to what is returned.
            horizon = max(int(self.cfg.get("fitness_horizon", 1)), 1)
            new, gamma = pfcm_step(self.X, centers, params)
            for _ in range(horizon-1):
                new, gamma = pfcm_step(self.X, new, params,
                                       gamma if self.cfg["gamma_refresh"] == "fixed" else None)
            d2 = squared_distance(self.X, new)
            if self.cfg.get("collapse_repair", False):
                new, repaired = repair_collapsed(self.X, new, d2, self.k)
                if repaired:
                    new, gamma = pfcm_step(self.X, new, params)
                    d2 = squared_distance(self.X, new)
            u, t, objective, _ = final_state(
                self.X, new, params, gamma if self.cfg["gamma_refresh"] == "fixed" else None)
            kind = self.cfg["fitness"]
            if kind == "fcm":
                scores[i] = (u**params["w"]*d2).sum()  # literal Eq.(6)
            elif kind == "fcm_reference":
                # Experimental correction: evaluate all genes on the SAME fuzzifier.
                # Gene w still affects the PFCM step, but cannot lower the score
                # simply by changing the exponent of the evaluation objective.
                ref_w = self.cfg.get("fitness_reference_w", 2.0)
                ref_u = memberships(d2, ref_w)
                scores[i] = (ref_u**ref_w*d2).sum()
            elif kind == "pfcm":
                scores[i] = objective  # Eq.(11) alternative assumption
            elif kind == "sse":
                scores[i] = d2.min(axis=1).sum()
            elif kind in ("ch", "db", "silhouette"):
                scores[i] = cvi_loss(self.X, d2.argmin(axis=1), kind)
            else:
                raise ValueError(f"Unknown fitness: {kind}")
            # Label-free collapse penalty. observed clusters < k needs no ground
            # truth to detect, so this is admissible inside the search. Scoring
            # multiplicatively keeps the ranking inside one deficiency level and
            # is free of the objective's own scale.
            cp = float(self.cfg.get("collapse_penalty", 0.0))
            if cp > 0.0:
                deficit = self.k - len(np.unique(d2.argmin(axis=1)))
                if deficit > 0:
                    scores[i] = abs(scores[i])*(1.0+cp)**deficit + cp*deficit
            if self.cfg["lamarckian"]:
                updated[i, :self.k*self.d] = new.ravel()
        self.evaluations += len(genes)
        if not np.isfinite(scores).all():
            raise FloatingPointError("Non-finite fitness; inspect parameter bounds.")
        return updated, scores

def fit_meta(X, k, rng, cfg, optimizer):
    anchors, dpc = density_peak_centers(X, k, cfg)
    problem = PFCMSearch(X, k, cfg)
    initial = problem.initial(anchors, rng, dpc.get("candidates"))
    best, best_fitness, trace = optimizer(problem, initial, rng, cfg)
    centers, params = problem.decode(best)
    final_cfg = dict(cfg, **params)
    result = solve_pfcm(X, centers, final_cfg)
    # The long final refinement is where clusters actually merge: a fuzzifier
    # that looks harmless after one step can collapse k clusters into fewer
    # over 100 iterations. observed clusters < k needs no ground truth, so
    # repairing here stays inside the unsupervised setting.
    guard_rounds = 0
    if cfg.get("final_collapse_guard", False):
        for _ in range(int(cfg.get("final_guard_max_rounds", 3))):
            d2 = squared_distance(X, result.centers)
            fixed, repaired = repair_collapsed(X, result.centers, d2, k)
            if not repaired:
                break
            guard_rounds += 1
            result = solve_pfcm(X, fixed, final_cfg)
    result.diagnostics.update({
        "final_collapse_guard": bool(cfg.get("final_collapse_guard", False)),
        "final_guard_rounds": guard_rounds,
        "fitness_horizon": int(cfg.get("fitness_horizon", 1)),
        "dpc": dpc, "best_fitness": float(best_fitness), "fitness_kind": cfg["fitness"],
        "fitness_evaluations": problem.evaluations, "optimizer_trace": trace,
        "best_chromosome": best.tolist(), "lamarckian": cfg["lamarckian"],
        "used_gpu": problem.use_gpu,
        "density_mode": cfg.get("density_mode", "gaussian"),
        "ks_neighbors": cfg.get("ks_neighbors", 7) if cfg.get("density_mode") == "local_scaled" else None,
        "init_mode": cfg.get("init_mode", "jitter"),
        "fitness_reference_w": cfg.get("fitness_reference_w", 2.0) if cfg["fitness"] == "fcm_reference" else None
    })
    return result
