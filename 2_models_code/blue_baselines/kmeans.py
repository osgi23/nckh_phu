"""BLUE | K-means: random observed centers, one Lloyd restart per run."""
import numpy as np
from common.numerics import ClusterResult, squared_distance

def fit(X, k, rng, cfg):
    centers = X[rng.choice(len(X), k, replace=False)].copy()
    trace = []
    for iteration in range(1, cfg["max_iter"]+1):
        d2 = squared_distance(X, centers)
        labels = d2.argmin(axis=1)
        new = centers.copy()
        used = set()
        for c in range(k):
            if np.any(labels == c):
                new[c] = X[labels == c].mean(axis=0)
            else:
                # Missing detail in paper: reseed empty clusters to worst residuals.
                order = np.argsort(-d2.min(axis=1), kind="stable")
                index = next(int(i) for i in order if int(i) not in used)
                used.add(index)
                new[c] = X[index]
        shift = float(np.max(np.abs(new-centers)))
        centers = new
        labels = squared_distance(X, centers).argmin(axis=1)
        objective = float(squared_distance(X, centers)[np.arange(len(X)), labels].sum())
        trace.append({"iteration": iteration, "objective": objective, "center_shift": shift})
        if shift <= cfg["tol"]:
            break
    return ClusterResult(centers, np.eye(k)[labels], objective=objective,
                         iterations=iteration, trace=trace,
                         diagnostics={"converged": shift <= cfg["tol"]})
