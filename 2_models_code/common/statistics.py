"""Kruskal-Wallis and two-sided Dunn-Bonferroni for actual repeat runs."""
import itertools
import numpy as np
from scipy.stats import kruskal, norm, rankdata
METRICS = ("accuracy_purity", "ari", "nmi")

def tests(rows, methods, datasets, alpha):
    omnibus, pairwise = [], []
    for dataset in datasets:
        for metric in METRICS:
            groups = {m: np.array([r[metric] for r in rows if r["dataset"] == dataset and r["method"] == m])
                      for m in methods}
            groups = {m:a for m,a in groups.items() if len(a) >= 5}
            if len(groups) < 2:
                omnibus.append({"dataset":dataset,"metric":metric,"status":"insufficient_runs_minimum_5"})
                continue
            names = list(groups)
            values = np.concatenate(list(groups.values()))
            H, p = (0.,1.) if np.all(values == values[0]) else kruskal(*groups.values())
            omnibus.append({"dataset":dataset,"metric":metric,"status":"ok","H":float(H),"p":float(p),"reject":bool(p<alpha)})
            ranks = rankdata(values, method="average")
            N = len(values)
            _, ties = np.unique(values,return_counts=True)
            variance = N*(N+1)/12 - np.sum(ties**3-ties)/(12*(N-1))
            mean_rank, offset = {}, 0
            for name in names:
                count = len(groups[name])
                mean_rank[name] = float(ranks[offset:offset+count].mean())
                offset += count
            family = len(names)*(len(names)-1)//2
            for first, second in itertools.combinations(names, 2):
                denominator = np.sqrt(max(variance,0)*(1/len(groups[first])+1/len(groups[second])))
                z = abs(mean_rank[first]-mean_rank[second])/denominator if denominator else 0.
                raw = float(2*norm.sf(z))
                adjusted = min(raw*family,1.)
                pairwise.append({"dataset":dataset,"metric":metric,"first":first,"second":second,
                    "z":float(z),"p_raw":raw,"p_bonferroni":adjusted,"family_size":family,
                    "reject":bool(adjusted<alpha),"omnibus_reject":bool(p<alpha),"interpret_posthoc":bool(p<alpha)})
    return omnibus, pairwise
