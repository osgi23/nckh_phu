"""Is the GA's fitness a useful surrogate for what the pipeline actually returns?

The GA scores a chromosome after ONE PFCM step. The pipeline then runs
solve_pfcm to convergence with that chromosome's own (a,b,w,eta) and reports
THAT. So the search ranks chromosomes by a one-step quantity while the user
receives the converged one.

This probe samples chromosomes exactly as the population is sampled, then for
each one records:
  surrogate   = the score the GA would assign (one PFCM step)
  converged   = the same FCM(w=2) objective AFTER solve_pfcm converges
  ari         = quality of the converged partition (reported only, never used
                by any search)

If rank correlation between surrogate and ari is near zero, improving the
search cannot improve the product, which would explain every negative result
so far.
"""
import copy
import json
import sys
from pathlib import Path

import numpy as np

CODE = Path("/home/user/nckh_phu/2_models_code")
sys.path.insert(0, str(CODE))

from common.data import load_dataset
from common.density_peak import density_peak_centers
from common.meta_pfcm import PFCMSearch
from common.metrics import quality
from common.numerics import memberships, solve_pfcm, squared_distance


def spearman(a, b):
    def rank(v):
        order = np.argsort(np.argsort(v, kind="stable"), kind="stable").astype(float)
        return order
    ra, rb = rank(np.asarray(a)), rank(np.asarray(b))
    ra -= ra.mean(); rb -= rb.mean()
    den = np.sqrt((ra**2).sum()*(rb**2).sum())
    return float((ra*rb).sum()/den) if den > 0 else float("nan")


BASE = json.loads((CODE/"configs"/"corrected_reference.json").read_text())
BASE["population"] = int(sys.argv[1]) if len(sys.argv) > 1 else 200
SLUGS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["iris", "wine", "glass", "ecoli"]

for slug in SLUGS:
    X, y, meta = load_dataset(slug)
    k = meta["paper_k"]
    anchors, dpc = density_peak_centers(X, k, BASE)
    problem = PFCMSearch(X, k, copy.deepcopy(BASE))
    rng = np.random.default_rng(12345)
    genes = problem.initial(anchors, rng, dpc.get("candidates"))
    _, surrogate = problem.evaluate(genes)

    converged, aris, clusters = [], [], []
    for gene in genes:
        centers, params = problem.decode(gene)
        res = solve_pfcm(X, centers, dict(BASE, **params))
        d2 = squared_distance(X, res.centers)
        u2 = memberships(d2, 2.0)
        converged.append(float((u2**2*d2).sum()))
        labels = res.labels(BASE["hard_labels"])
        aris.append(quality(y, labels)["ari"])
        clusters.append(len(np.unique(labels)))

    print(json.dumps({
        "dataset": slug, "k": k, "population": len(genes),
        "rho_surrogate_vs_ari": spearman(surrogate, aris),
        "rho_converged_vs_ari": spearman(converged, aris),
        "rho_surrogate_vs_converged": spearman(surrogate, converged),
        "ari_min": min(aris), "ari_max": max(aris), "ari_mean": float(np.mean(aris)),
        "ari_of_best_surrogate": aris[int(np.argmin(surrogate))],
        "ari_of_best_converged": aris[int(np.argmin(converged))],
        "collapsed_fraction": float(np.mean([c < k for c in clusters])),
    }), flush=True)
