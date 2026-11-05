"""Consensus clustering over a label-free ensemble of DP-PFCM solutions.

Motivation measured in this project: DP-GA-PFCM and a fuzzifier sweep disagree
a lot per dataset, and taking the better of the two per dataset would score
0.5699 mean ARI against the paper's 0.5581 - but choosing by ARI would use the
labels. Consensus COMBINES the members instead of choosing between them, so it
needs no labels.

Two measured facts shape the design:

  * A large fuzzifier merges clusters, and every internal index tried here
    (Calinski-Harabasz, Davies-Bouldin, silhouette, resampling stability)
    prefers those merged partitions. Restricting the ensemble to members that
    realise k clusters was worth +0.10 mean ARI on the development suite, so
    the same filter is applied here. k is given in this problem setting, so the
    filter uses no labels.
  * Members that collapse carry no information about how the k real groups
    split, so dropping them removes noise rather than signal.

Combination follows the co-association route of Fred & Jain: the fraction of
members in which two points share a cluster becomes a similarity, and an
average-linkage cut at k turns it back into a partition.
"""
import numpy as np
from sklearn.cluster import AgglomerativeClustering

from common.density_peak import density_peak_centers
from common.numerics import random_partition_centers, solve_fcm, solve_pfcm

DEFAULT_FUZZIFIERS = (1.1, 1.2, 1.5, 2.0, 3.0, 5.0)


def _labels_of(result, cfg):
    return result.labels(cfg.get("hard_labels", "membership"))


def select_fuzzifier(X, k, cfg, rng, fuzzifiers=DEFAULT_FUZZIFIERS,
                     subsamples=8, fraction=0.8):
    """Pick a fuzzifier without using labels: most reproducible under
    resampling, among the settings that actually realise k clusters.

    Measured on the development suite: the k-constraint is what makes this work
    at all. Unconstrained, resampling stability scored 0.4418 mean ARI and
    Calinski-Harabasz 0.4157, both WORSE than simply fixing w = 2 (0.4390),
    because a merged partition is the most reproducible one. With the
    constraint, stability reached 0.5398, i.e. 98.8% of the label-aware oracle.

    Returns (w, diagnostics).
    """
    from itertools import combinations

    from sklearn.metrics import adjusted_rand_score

    n = len(X)
    size = max(int(fraction*n), k+1)
    draws = [np.sort(rng.choice(n, size, replace=False)) for _ in range(int(subsamples))]
    rows = []
    for w in fuzzifiers:
        anchors, _ = density_peak_centers(X, k, cfg)
        full = _labels_of(solve_pfcm(X, anchors.copy(),
                                     dict(cfg, a=1.0, b=1.0, w=float(w), eta=2.0)), cfg)
        parts = []
        for index in draws:
            sub_anchors, _ = density_peak_centers(X[index], k, cfg)
            sub = _labels_of(solve_pfcm(X[index], sub_anchors.copy(),
                                        dict(cfg, a=1.0, b=1.0, w=float(w), eta=2.0)), cfg)
            mapped = np.full(n, -1)
            mapped[index] = sub
            parts.append(mapped)
        scores = []
        for a, b in combinations(range(len(parts)), 2):
            both = (parts[a] >= 0) & (parts[b] >= 0)
            if both.sum() > k:
                scores.append(adjusted_rand_score(parts[a][both], parts[b][both]))
        rows.append({"w": float(w), "clusters": int(len(np.unique(full))),
                     "stability": float(np.mean(scores)) if scores else -np.inf})
    pool = [r for r in rows if r["clusters"] == k] or rows
    best = max(pool, key=lambda r: r["stability"])
    return best["w"], {"profile": rows, "full_k_candidates": len(pool),
                       "fell_back": not any(r["clusters"] == k for r in rows)}


def pin_fuzzifier(cfg, w, slack=0.02):
    """Return a copy of cfg whose search bounds confine w to a point.

    The optimiser then spends its whole budget on the centres and on a, b, eta
    instead of on the one parameter a label-free criterion can already fix.
    Bounds keep a small width because the config validator requires low < high.
    """
    low, high = cfg["parameter_bounds"]["w"]
    centre = float(min(max(w, low+slack), high-slack))
    out = dict(cfg)
    out["parameter_bounds"] = dict(cfg["parameter_bounds"],
                                   w=[centre-slack, centre+slack])
    out["w"] = centre
    return out


def ensemble_members(X, k, cfg, rng, fuzzifiers=DEFAULT_FUZZIFIERS,
                     subsamples=0, subsample_fraction=0.8, include_fcm=False):
    """Build the ensemble. Returns a list of (labels, mask) over the full index.

    mask marks which points the member actually clustered, so members fitted on
    a subsample only vote on the pairs they saw.
    """
    n = len(X)
    members = []
    anchors, _ = density_peak_centers(X, k, cfg)
    for w in fuzzifiers:
        result = solve_pfcm(X, anchors.copy(), dict(cfg, a=1.0, b=1.0, w=float(w), eta=2.0))
        members.append((_labels_of(result, cfg), np.ones(n, dtype=bool)))

    if include_fcm:
        # A non-possibilistic member adds diversity: FCM has no typicality term,
        # so it fails differently from every PFCM member.
        for w in (1.5, 2.0):
            centres = random_partition_centers(X, k, rng, w)
            result = solve_fcm(X, centres, w=float(w), max_iter=cfg["max_iter"], tol=cfg["tol"])
            members.append((_labels_of(result, cfg), np.ones(n, dtype=bool)))

    for _ in range(int(subsamples)):
        size = max(int(subsample_fraction*n), k+1)
        index = np.sort(rng.choice(n, size, replace=False))
        sub_anchors, _ = density_peak_centers(X[index], k, cfg)
        w = float(rng.choice(fuzzifiers))
        result = solve_pfcm(X[index], sub_anchors.copy(),
                            dict(cfg, a=1.0, b=1.0, w=w, eta=2.0))
        full = np.full(n, -1)
        full[index] = _labels_of(result, cfg)
        mask = np.zeros(n, dtype=bool)
        mask[index] = True
        members.append((full, mask))
    return members


def co_association(members, n, k, require_full_k=True):
    """Average co-assignment over the retained members.

    Returns (matrix, kept) where kept is how many members survived the filter.
    """
    total = np.zeros((n, n))
    seen = np.zeros((n, n))
    kept = 0
    for labels, mask in members:
        present = np.unique(labels[mask])
        if require_full_k and len(present) != k:
            continue
        kept += 1
        m = mask.astype(float)
        seen += np.outer(m, m)
        same = (labels[:, None] == labels[None, :]).astype(float)
        total += same*np.outer(m, m)
    if kept == 0:
        return None, 0
    with np.errstate(invalid="ignore", divide="ignore"):
        matrix = np.where(seen > 0, total/np.maximum(seen, 1e-12), 0.0)
    np.fill_diagonal(matrix, 1.0)
    return matrix, kept


def consensus_labels(X, k, cfg, rng, fuzzifiers=DEFAULT_FUZZIFIERS, subsamples=0,
                     include_fcm=False, require_full_k=True, refine=False):
    """Full pipeline. Returns (labels, diagnostics). No labels are read."""
    n = len(X)
    members = ensemble_members(X, k, cfg, rng, fuzzifiers=fuzzifiers,
                               subsamples=subsamples, include_fcm=include_fcm)
    matrix, kept = co_association(members, n, k, require_full_k=require_full_k)
    fallback = False
    if matrix is None:
        # No member realised k clusters. Rather than return nothing, drop the
        # filter and record that it happened.
        matrix, kept = co_association(members, n, k, require_full_k=False)
        fallback = True
    distance = 1.0-matrix
    np.fill_diagonal(distance, 0.0)
    distance = np.maximum(distance, 0.0)
    model = AgglomerativeClustering(n_clusters=k, metric="precomputed", linkage="average")
    labels = model.fit_predict(distance)

    info = {"members": len(members), "members_kept": kept,
            "filter_fallback": fallback, "refined": False}
    if refine:
        # Optional: hand the consensus partition back to PFCM as an
        # initialisation. Reported as a separate variant because it can change
        # the partition shape.
        centres = np.vstack([X[labels == c].mean(axis=0) if (labels == c).any()
                             else X[rng.integers(n)] for c in range(k)])
        result = solve_pfcm(X, centres, dict(cfg, a=1.0, b=1.0, w=2.0, eta=2.0))
        refined = _labels_of(result, cfg)
        if len(np.unique(refined)) == k:
            labels = refined
            info["refined"] = True
    info["clusters"] = int(len(np.unique(labels)))
    return labels, info
