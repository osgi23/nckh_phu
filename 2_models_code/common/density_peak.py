"""DPC initialization: Gaussian density (2), delta (3), top rho*delta."""
import numpy as np
from scipy.spatial.distance import cdist, pdist

def density_peak_centers(X, k, cfg):
    n = len(X)
    if not 1 <= k <= n:
        raise ValueError("Invalid k for density peak.")
    q = cfg["dc_quantile"]
    if n <= cfg["dc_exact_limit"]:
        distances = pdist(X)
        mode = "exact_all_unordered_pairs"
    else:
        # Only dc uses sampling. Rho and delta still use ALL observations.
        # Fixed independent seed ensures all optimizers use the same DPC.
        rng = np.random.default_rng(0)
        count = cfg["dc_sample_pairs"]
        left = rng.integers(0, n, count)
        right = (left + rng.integers(1, n, count)) % n
        distances = np.linalg.norm(X[left]-X[right], axis=1)
        mode = "sampled_pairs_for_dc_only"
    dc = float(np.quantile(distances, q)) if len(distances) else 1.0
    if dc <= 1e-12:
        positive = distances[distances > 1e-12]
        dc = float(positive.min()) if len(positive) else 1.0
    pairs = len(distances)
    del distances
    block = cfg["dpc_block_size"]
    rho = np.empty(n)
    for start in range(0, n, block):
        end = min(start+block, n)
        d2 = cdist(X[start:end], X, metric="sqeuclidean")
        rho[start:end] = np.exp(-d2/(dc*dc)).sum(axis=1)-1.0
    delta = np.empty(n)
    for start in range(0, n, block):
        end = min(start+block, n)
        d2 = cdist(X[start:end], X, metric="sqeuclidean")
        higher = rho[None, :] > rho[start:end, None]
        nearest = np.where(higher, d2, np.inf).min(axis=1)
        top = ~higher.any(axis=1)
        nearest[top] = d2[top].max(axis=1)
        delta[start:end] = np.sqrt(nearest)
    score = rho*delta
    order = np.argsort(-score, kind="stable")
    chosen, seen = [], set()
    for index in order:
        point = tuple(X[index])
        if point not in seen:
            chosen.append(int(index))
            seen.add(point)
        if len(chosen) == k:
            break
    if len(chosen) < k:
        raise ValueError("k exceeds the number of distinct feature vectors.")
    return X[chosen].copy(), {"dc": dc, "dc_mode": mode, "dc_pairs": pairs,
                             "indices": chosen, "rho": rho.tolist(), "delta": delta.tolist()}
