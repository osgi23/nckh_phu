"""Equations (7)-(12), corrected cluster indices; all arrays are float64."""
from dataclasses import dataclass, field
import numpy as np
from scipy.spatial.distance import cdist

EPS = 1e-12

@dataclass
class ClusterResult:
    centers: np.ndarray
    membership: np.ndarray
    typicality: np.ndarray | None = None
    objective: float = 0.0
    iterations: int = 0
    params: dict = field(default_factory=dict)
    trace: list = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)

    def labels(self, rule="membership"):
        if rule == "typicality" and self.typicality is not None:
            return np.argmax(self.typicality, axis=1)
        return np.argmax(self.membership, axis=1)

def squared_distance(X, centers):
    return cdist(X, centers, metric="sqeuclidean")

def memberships(d2, w):
    if not np.isfinite(w) or w <= 1:
        raise ValueError("w must be finite and > 1.")
    # Log normalization prevents overflow close to w=1.
    log_u = -np.log(np.maximum(d2, EPS)) / (w - 1)
    log_u -= log_u.max(axis=1, keepdims=True)
    u = np.exp(log_u)
    u /= u.sum(axis=1, keepdims=True)
    zeros = d2 <= EPS
    hit = zeros.any(axis=1)
    # Coincident centers share the mass; do not arbitrarily prefer one.
    u[hit] = zeros[hit] / zeros[hit].sum(axis=1, keepdims=True)
    return u

def gamma_values(u, d2, w, scale):
    return np.maximum(scale * (u**w * d2).sum(axis=0) /
                      np.maximum((u**w).sum(axis=0), EPS), EPS)

def typicalities(d2, gamma, b, eta):
    if b <= 0 or eta <= 1:
        raise ValueError("b > 0 and eta > 1 are required.")
    log_ratio = (np.log(np.maximum(b*d2, EPS)) - np.log(gamma)[None, :])/(eta-1)
    t = np.exp(-np.logaddexp(0, log_ratio))
    t[d2 <= EPS] = 1.0
    return t

def weighted_centers(X, weights, old):
    total = weights.sum(axis=0)
    centers = weights.T @ X / np.maximum(total[:, None], EPS)
    centers[total <= EPS] = old[total <= EPS]
    return centers

def pfcm_step(X, centers, params, gamma=None):
    """One inner iteration: U,T from current V -> update V once."""
    a, b, w, eta = (params[q] for q in ("a", "b", "w", "eta"))
    if a <= 0 or b <= 0 or w <= 1 or eta <= 1:
        raise ValueError("Invalid PFCM parameters.")
    d2 = squared_distance(X, centers)
    u = memberships(d2, w)
    if gamma is None:
        gamma = gamma_values(u, d2, w, params["gamma_scale"])
    t = typicalities(d2, gamma, b, eta)
    new = weighted_centers(X, a*u**w + b*t**eta, centers)
    return new, gamma

def final_state(X, centers, params, gamma=None):
    d2 = squared_distance(X, centers)
    u = memberships(d2, params["w"])
    if gamma is None:
        gamma = gamma_values(u, d2, params["w"], params["gamma_scale"])
    t = typicalities(d2, gamma, params["b"], params["eta"])
    objective = ((params["a"]*u**params["w"] + params["b"]*t**params["eta"])*d2).sum()
    objective += (gamma * ((1-t)**params["eta"]).sum(axis=0)).sum()
    return u, t, float(objective), gamma

def stopping_measure(previous, current, shift, criterion, mode):
    if criterion not in ("objective", "centers") or mode not in ("absolute", "relative"):
        raise ValueError("Invalid stopping criterion/mode.")
    delta = abs(current-previous)
    measure = delta/max(abs(previous), EPS) if mode == "relative" else delta
    return (shift if criterion == "centers" else measure), delta

def solve_fcm(X, centers, w=2.0, max_iter=100, tol=1e-6,
              stop_criterion="objective", stop_mode="absolute"):
    if max_iter < 1 or not np.isfinite(tol) or tol < 0:
        raise ValueError("max_iter >= 1 and finite tol >= 0 required.")
    centers = centers.copy()
    d2 = squared_distance(X, centers)
    u = memberships(d2, w)
    previous = float((u**w*d2).sum())
    trace = []
    for iteration in range(1, max_iter+1):
        new = weighted_centers(X, u**w, centers)
        shift = float(np.max(np.abs(new-centers)))
        centers = new
        d2 = squared_distance(X, centers)
        u = memberships(d2, w)
        objective = float((u**w*d2).sum())
        measure, delta = stopping_measure(previous, objective, shift, stop_criterion, stop_mode)
        trace.append({"iteration": iteration, "objective": objective, "center_shift": shift,
                      "objective_change": delta, "stopping_measure": measure})
        if measure <= tol:
            break
        previous = objective
    return ClusterResult(centers, u, objective=objective, iterations=iteration,
                         params={"w": w}, trace=trace,
                         diagnostics={"converged": measure <= tol,
                                      "stop_criterion": stop_criterion, "stop_mode": stop_mode,
                                      "stop_reason": "tolerance" if measure <= tol else "max_iter"})

def solve_pfcm(X, centers, cfg):
    params = {q: float(cfg[q]) for q in ("a", "b", "w", "eta", "gamma_scale")}
    if not all(np.isfinite(v) for v in params.values()) or params["gamma_scale"] <= 0:
        raise ValueError("Finite PFCM parameters and gamma_scale > 0 required.")
    if cfg["max_iter"] < 1 or not np.isfinite(cfg["tol"]) or cfg["tol"] < 0:
        raise ValueError("max_iter >= 1 and finite tol >= 0 required.")
    criterion = cfg.get("stop_criterion", "objective")
    mode = cfg.get("stop_mode", "absolute")
    centers = centers.copy()
    _, _, previous, initial_gamma = final_state(X, centers, params)
    gamma = initial_gamma if cfg["gamma_refresh"] == "fixed" else None
    trace = []
    for iteration in range(1, cfg["max_iter"]+1):
        if cfg["gamma_refresh"] == "each_step":
            gamma = None
        new, gamma = pfcm_step(X, centers, params, gamma)
        shift = float(np.max(np.abs(new-centers)))
        centers = new
        u, t, objective, final_gamma = final_state(
            X, centers, params, gamma if cfg["gamma_refresh"] == "fixed" else None)
        measure, delta = stopping_measure(previous, objective, shift, criterion, mode)
        trace.append({"iteration": iteration, "objective": objective, "center_shift": shift,
                      "objective_change": delta, "stopping_measure": measure})
        if measure <= cfg["tol"]:
            break
        previous = objective
    return ClusterResult(centers, u, t, objective, iteration, params, trace,
                         {"converged": measure <= cfg["tol"], "gamma": final_gamma.tolist(),
                          "stop_criterion": criterion, "stop_mode": mode,
                          "stop_reason": "tolerance" if measure <= cfg["tol"] else "max_iter"})

def random_partition_centers(X, k, rng, w):
    """Unspecified baseline initialization: normalized random membership."""
    u = rng.random((len(X), k))
    u /= u.sum(axis=1, keepdims=True)
    fallback = X[rng.choice(len(X), k, replace=False)]
    return weighted_centers(X, u**w, fallback)
