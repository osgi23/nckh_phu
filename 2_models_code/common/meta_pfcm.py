"""Common DP -> optimize [centers,a,b,w,eta] -> final PFCM pipeline."""
import numpy as np
from common.density_peak import density_peak_centers
from common.numerics import pfcm_step, final_state, squared_distance, solve_pfcm, memberships

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
        if self.device in ("cuda", "gpu", "auto") and cfg.get("use_gpu", True):
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

    def initial(self, anchors, rng):
        size = self.cfg["population"]
        genes = rng.uniform(self.low, self.high, (size, len(self.low)))
        centers = anchors[None, :, :] + rng.normal(
            0, self.cfg["seed_jitter"], (size, self.k, self.d))
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
            new, gamma = pfcm_step(self.X, centers, params)
            u, t, objective, _ = final_state(
                self.X, new, params, gamma if self.cfg["gamma_refresh"] == "fixed" else None)
            d2 = squared_distance(self.X, new)
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
            else:
                raise ValueError(f"Unknown fitness: {kind}")
            if self.cfg["lamarckian"]:
                updated[i, :self.k*self.d] = new.ravel()
        self.evaluations += len(genes)
        if not np.isfinite(scores).all():
            raise FloatingPointError("Non-finite fitness; inspect parameter bounds.")
        return updated, scores

def fit_meta(X, k, rng, cfg, optimizer):
    anchors, dpc = density_peak_centers(X, k, cfg)
    problem = PFCMSearch(X, k, cfg)
    initial = problem.initial(anchors, rng)
    best, best_fitness, trace = optimizer(problem, initial, rng, cfg)
    centers, params = problem.decode(best)
    final_cfg = dict(cfg, **params)
    result = solve_pfcm(X, centers, final_cfg)
    result.diagnostics.update({
        "dpc": dpc, "best_fitness": float(best_fitness), "fitness_kind": cfg["fitness"],
        "fitness_evaluations": problem.evaluations, "optimizer_trace": trace,
        "best_chromosome": best.tolist(), "lamarckian": cfg["lamarckian"],
        "used_gpu": problem.use_gpu,
        "fitness_reference_w": cfg.get("fitness_reference_w", 2.0) if cfg["fitness"] == "fcm_reference" else None
    })
    return result
