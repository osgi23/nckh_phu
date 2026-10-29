"""Paired Gaussian mixtures with replacement contamination; labels used only for scoring."""
import numpy as np
from scipy.optimize import linear_sum_assignment
from common.metrics import quality

def seed_for(seed, replicate, tag):
    return int(np.random.SeedSequence([seed, replicate, tag]).generate_state(1)[0])

def condition_slug(rate):
    return f"outliers_{100*rate:05.2f}pct".replace(".", "p")

def make_replicate(study, replicate):
    """Generate all contamination levels from the same clean data and outlier pool."""
    n, nc, dimensions = study["n_samples"], study["Nc"], study["L"]
    rng = np.random.default_rng(seed_for(study["seed"], replicate, 1))
    direction = np.ones(dimensions)/np.sqrt(dimensions)
    centers = (np.arange(nc)-(nc-1)/2)[:,None]*study["center_separation"]*direction[None,:]
    balance_index = replicate // study.get("datasets_per_balance", 3)
    weights = np.asarray(study["balance_levels"][balance_index], dtype=float)
    counts = np.floor(n*weights).astype(int)
    for j in np.argsort(-(n*weights-counts))[:n-counts.sum()]:
        counts[j] += 1
    y = np.repeat(np.arange(nc), counts)
    y = y[rng.permutation(n)]
    X = centers[y] + rng.normal(0, study["cluster_std"], size=(n, dimensions))
    # Weighted replacement keeps each retained Gaussian component represented.
    groups = [rng.permutation(np.flatnonzero(y == c)).tolist() for c in range(nc)]
    priority = sorted(((j+.5)/len(group), index) for group in groups for j,index in enumerate(group))
    replacement = np.array([index for _,index in priority],dtype=int)
    out_rng = np.random.default_rng(seed_for(study["seed"], replicate, 2))
    pool = []
    while len(pool) < n:
        candidates = out_rng.uniform(-study["outlier_box"], study["outlier_box"], size=(n, dimensions))
        minimum = np.linalg.norm(candidates[:,None,:]-centers[None,:,:], axis=2).min(axis=1)
        pool.extend(candidates[minimum >= study["outlier_min_distance"]])
    pool = np.asarray(pool[:n])
    arrays = {"X_clean": X, "y_clean": y, "true_centers": centers, "replacement_order": replacement,
              "outlier_pool": pool}
    for condition in study["conditions"]:
        slug = condition["slug"]
        count = condition["n_outliers"]
        contaminated = X.copy()
        truth = y.copy()
        index = replacement[:count]
        contaminated[index] = pool[index]
        truth[index] = -1
        minimum, maximum = contaminated.min(axis=0), contaminated.max(axis=0)
        span = np.where(maximum > minimum, maximum-minimum, 1.)
        arrays["X_raw_"+slug] = contaminated
        arrays["X_scaled_"+slug] = (contaminated-minimum)/span
        arrays["y_"+slug] = truth
        arrays["min_"+slug] = minimum
        arrays["span_"+slug] = span
    return arrays

def score_fit(truth, predicted, centers_raw, true_centers):
    mask = truth >= 0
    if not mask.any():
        raise ValueError("No inliers are available for evaluation.")
    scores = quality(truth[mask], predicted[mask])
    distance = ((centers_raw[:,None,:]-true_centers[None,:,:])**2).sum(axis=2)
    rows, columns = linear_sum_assignment(distance)
    if len(rows) != len(true_centers):
        raise ValueError("Number of centers differs from Nc.")
    scores["center_rmse"] = float(np.sqrt(np.mean((centers_raw[rows]-true_centers[columns])**2)))
    scores["observed_clusters_all"] = int(len(np.unique(predicted)))
    return scores

def make_study(nc=2, dimensions=5, samples=500, rates=(0., .05, .1, .2), seed=2026):
    if nc < 2 or dimensions < 1 or samples < nc:
        raise ValueError("Nc >= 2, L >= 1 and n_samples >= Nc required.")
    if not rates or len(set(rates)) != len(rates) or 0. not in rates:
        raise ValueError("Rates must be distinct and include the 0% control.")
    if any(not np.isfinite(r) or not 0 <= r < 1 for r in rates):
        raise ValueError("Every outlier rate must be finite and in [0, 1).")
    conditions = []
    for rate in sorted(rates):
        count = int(round(samples*rate))
        if samples-count < nc:
            raise ValueError("Too few inliers remain for Nc clusters.")
        conditions.append({"slug": condition_slug(rate), "requested_ratio": rate,
                           "actual_ratio": count/samples, "n_outliers": count,
                           "n_inliers": samples-count})
    if len({c["n_outliers"] for c in conditions}) != len(conditions):
        raise ValueError("Rates round to identical counts; increase sample count.")
    return {"Nc": nc, "L": dimensions, "n_samples": samples, "seed": seed,
            "cluster_std": 1., "center_separation": 4.,
            "outlier_box": max(8., (nc-1)*2/np.sqrt(dimensions)+6.),
            "outlier_min_distance": 4., "conditions": conditions,
            "contamination": "Replace points by uniform box draws conditioned on Euclidean distance >= 4 from every true center; fixed total n.",
            "pairing": "Nine independent datasets (3 per balance); each held fixed for 25 independent algorithm restarts. Same clean points and nested outlier masks across contamination levels; methods share data and fit seed.",
            "metrics_scope": "Purity, ARI and geometric NMI only on y >= 0 (Gaussian inliers). No outlier detection score; all methods assign every sample.",
            "centers": "Nc equally spaced means along the unit all-ones direction; adjacent Euclidean separation=4; each covariance=I_L.",
            "preprocessing": "Featurewise min-max on the complete contaminated data separately for each replicate/condition; shared by all methods.",
            "known_k": "Every method receives k=Nc. This experiment does not estimate Nc.",
            "balance_levels": [[1/nc]*nc, [.7]+[.3/(nc-1)]*(nc-1), [.9]+[.1/(nc-1)]*(nc-1)],
            "datasets_per_balance": 3, "n_datasets": 9,
            "balance_assumption": "50/50, 70/30, 90/10 for Nc=2 are chosen here; not specified in supplied excerpt."}
