"""Minimal ablation for AF-NKGA (research note, section 6).

Variants, one factor changed at a time:

  A0  original graph (plain Euclidean), fuzzy off, random population
  A1  original graph,                   fuzzy off, population seeded from the bank
  A2  adaptive graph (local scaling),   fuzzy off, population seeded from the bank
  A3  original graph,                   fuzzy ON,  population seeded from the bank
  A4  adaptive graph,                   fuzzy ON,  population seeded from the bank

A1 vs A3 and A2 vs A4 are the controlled lambda-on/off pairs: identical graph,
identical bank, identical starting population (init_local_search=False keeps the
population bit-identical, since local search would otherwise consult the
fitness being compared).

The reference bank is DP-PFCM from this project, so the fuzzy evidence comes
from the same code the reproduction uses. Ground-truth labels are read only
after the search returns.

Usage: python -m afnkga.run --datasets iris wine --runs 3
"""
import argparse
import copy
import json
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from afnkga.ga import run as ga_run
from afnkga.model import Fitness, Graph, fuzzy_evidence
from common.data import load_dataset
from common.metrics import quality
from common.registry import fit_method

ROOT = Path(__file__).resolve().parents[1]

VARIANTS = {
    "A0": {"adaptive": False, "lam": 0.0, "seeded": False},
    "A1": {"adaptive": False, "lam": 0.0, "seeded": True},
    "A2": {"adaptive": True, "lam": 0.0, "seeded": True},
    "A3": {"adaptive": False, "lam": 0.4, "seeded": True},
    "A4": {"adaptive": True, "lam": 0.4, "seeded": True},
}


def build_bank(X, k, cfg, rng, sizes):
    """DP-PFCM reference models at several cluster counts.

    Equal total weight per cluster count, so one C_ref cannot get more votes by
    appearing with more seeds (research note, module M3).
    """
    bank, labels = [], []
    for c in sizes:
        if not 2 <= c <= len(np.unique(X, axis=0)):
            continue
        result = fit_method("DP-PFCM", X, c, np.random.default_rng(rng.integers(2**32)),
                            copy.deepcopy(cfg))
        bank.append((result.membership, result.typicality))
        labels.append(result.labels("membership")+1)   # 0 is reserved for noise
    if not bank:
        raise ValueError("Could not build any reference model.")
    return bank, labels


def score(y, z):
    """Two conventions, both reported; never mix them in one number.

    all   - every point counts, noise forms its own cluster
    inlier- only points the algorithm did not call noise, with its coverage
    """
    z = np.asarray(z)
    out = {"ari_all": float(adjusted_rand_score(y, z)),
           "nmi_all": float(normalized_mutual_info_score(y, z, average_method="geometric")),
           "noise_fraction": float((z == 0).mean()),
           "clusters_found": int(len(np.unique(z[z > 0])))}
    keep = z > 0
    if keep.sum() > 1 and len(np.unique(y[keep])) > 1:
        inlier = quality(y[keep], z[keep])
        out.update({"ari_inlier": inlier["ari"], "purity_inlier": inlier["accuracy_purity"],
                    "inlier_coverage": float(keep.mean())})
    else:
        out.update({"ari_inlier": float("nan"), "purity_inlier": float("nan"),
                    "inlier_coverage": float(keep.mean())})
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", nargs="+", default=["iris"])
    parser.add_argument("--variants", nargs="+", default=list(VARIANTS))
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--population", type=int, default=30)
    parser.add_argument("--generations", type=int, default=40)
    parser.add_argument("--neighbours", type=int, default=3, help="NK group size K")
    parser.add_argument("--ks", type=int, default=7, help="neighbour index for local scaling")
    parser.add_argument("--lam", type=float, default=None, help="override lambda")
    parser.add_argument("--balance", action="store_true",
                        help="rebalance b against a (see fuzzy_evidence); the NK edge set "
                             "makes b 100x scarcer than a, which otherwise lets the fuzzy "
                             "term push toward merging just like the NK term")
    parser.add_argument("--config", type=Path, default=ROOT/"configs"/"corrected_reference.json")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args(argv)

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    cfg["population"], cfg["generations"] = 20, 10      # bank only, not the NK search

    for slug in args.datasets:
        X, y, meta = load_dataset(slug)
        k = meta["paper_k"]
        # Bank sizes bracket k without being read off the true class count.
        sizes = sorted({max(2, k-1), k, k+1})
        for run in range(args.runs):
            seed = int(np.random.SeedSequence(
                [args.seed, meta["table1_order"], run]).generate_state(1)[0])
            bank_rng = np.random.default_rng(seed)
            bank, bank_labels = build_bank(X, k, cfg, bank_rng, sizes)
            graphs = {flag: Graph(X, neighbours=args.neighbours, ks=args.ks, adaptive=flag)
                      for flag in {VARIANTS[v]["adaptive"] for v in args.variants}}
            for name in args.variants:
                spec = VARIANTS[name]
                lam = spec["lam"] if args.lam is None else (args.lam if spec["lam"] > 0 else 0.0)
                graph = graphs[spec["adaptive"]]
                evidence = fuzzy_evidence(graph, bank, balance=args.balance) if lam > 0 else None
                fitness = Fitness(graph, evidence, lam=lam)
                started = time.perf_counter()
                best, best_f, trace = ga_run(
                    fitness, np.random.default_rng(seed),
                    seeds=bank_labels if spec["seeded"] else (),
                    population=args.population, generations=args.generations,
                    init_local_search=False)
                elapsed = time.perf_counter()-started
                print(json.dumps({
                    "dataset": slug, "variant": name, "run": run+1, "seed": seed,
                    "k_true": k, "adaptive": spec["adaptive"], "lam": lam,
                    "seeded": spec["seeded"], "balance": bool(args.balance), "fitness": best_f,
                    "fitness_gen0": trace[0]["best_fitness"],
                    "evaluations": fitness.evaluations, "seconds": elapsed,
                    **score(y, best)}), flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
