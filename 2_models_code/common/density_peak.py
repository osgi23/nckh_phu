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
    density_mode = cfg.get("density_mode", "gaussian")
    if density_mode not in ("gaussian", "local_scaled"):
        raise ValueError("density_mode: gaussian or local_scaled.")
    sigma = None
    if density_mode == "local_scaled":
        # Local scaling of Zelnik-Manor & Perona (NIPS 2004): sigma_i is the
        # distance to the ks-th nearest neighbour, so density is dimensionless
        # and no single global dc has to fit clusters of different densities.
        ks = min(max(int(cfg.get("ks_neighbors", 7)), 1), n-1)
        sigma = np.empty(n)
        for start in range(0, n, block):
            end = min(start+block, n)
            d2 = cdist(X[start:end], X, metric="sqeuclidean")
            # Column ks after partition: index 0 is the point itself (d=0).
            sigma[start:end] = np.sqrt(np.partition(d2, ks, axis=1)[:, ks])
        sigma = np.maximum(sigma, 1e-12)
    for start in range(0, n, block):
        end = min(start+block, n)
        d2 = cdist(X[start:end], X, metric="sqeuclidean")
        if sigma is None:
            rho[start:end] = np.exp(-d2/(dc*dc)).sum(axis=1)-1.0
        else:
            scale = sigma[start:end, None]*sigma[None, :]
            rho[start:end] = np.exp(-d2/scale).sum(axis=1)-1.0
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
    # Keep a longer ranked list of distinct candidates so a population can be
    # seeded from several plausible peak sets, not only from the single top-k.
    want = min(n, max(int(cfg.get("candidate_pool", 4))*k, k))
    candidates, seen = [], set()
    for index in order:
        point = tuple(X[index])
        if point not in seen:
            candidates.append(int(index))
            seen.add(point)
        if len(candidates) == want:
            break
    chosen = candidates[:k]
    if len(chosen) < k:
        raise ValueError("k exceeds the number of distinct feature vectors.")
    return X[chosen].copy(), {"dc": dc, "dc_mode": mode, "dc_pairs": pairs,
                             "indices": chosen, "rho": rho.tolist(), "delta": delta.tolist(),
                             "density_mode": density_mode, "candidates": candidates}
