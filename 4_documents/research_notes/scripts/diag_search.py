"""Error analysis: does the GA search actually move, and where does quality come from?

Protocol mirrors common/runner.py exactly: same seed derivation
(SeedSequence([cfg.seed, table1_order, run])), same k_policy, same scaling,
same config file. Ground-truth labels are used ONLY after fit, for reporting.

Writes one JSON record per (dataset, method, run) to stdout as JSONL.
"""
import copy
import json
import sys
import time
from pathlib import Path

import numpy as np

CODE = Path("/home/user/nckh_phu/2_models_code")
sys.path.insert(0, str(CODE))

from common.data import load_dataset, dataset_names
from common.density_peak import density_peak_centers
from common.metrics import quality
from common.numerics import squared_distance
from common.registry import fit_method

CFG = json.loads((CODE / "configs" / "corrected_reference.json").read_text())
CFG["population"] = int(sys.argv[1]) if len(sys.argv) > 1 else 80
CFG["generations"] = int(sys.argv[2]) if len(sys.argv) > 2 else 100
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 5
METHODS = sys.argv[4].split(",") if len(sys.argv) > 4 else ["DP-GA-PFCM", "DP-PSO-PFCM"]
GROUP = sys.argv[5] if len(sys.argv) > 5 else "su_dung"

for slug in dataset_names(GROUP):
    X, y, meta = load_dataset(slug)
    k = meta["paper_k"] if CFG["k_policy"] == "paper" else meta["observed_classes"]

    # Label-free diagnostic of the initialization itself: DPC anchors are
    # deterministic, so hard-assign every point to its nearest anchor.
    anchors, dpc = density_peak_centers(X, k, CFG)
    init_labels = squared_distance(X, anchors).argmin(axis=1)
    print(json.dumps({
        "dataset": slug, "method": "DPC-init-only", "run": 0, "k": k,
        "n": int(len(X)), "d": int(X.shape[1]),
        "observed_classes": meta["observed_classes"],
        **quality(y, init_labels),
    }), flush=True)

    for run in range(RUNS):
        seed = int(np.random.SeedSequence(
            [CFG["seed"], meta["table1_order"], run]).generate_state(1)[0])
        for name in METHODS:
            started = time.perf_counter()
            res = fit_method(name, X, k, np.random.default_rng(seed), copy.deepcopy(CFG))
            elapsed = time.perf_counter() - started
            labels = res.labels(CFG["hard_labels"])
            trace = res.diagnostics["optimizer_trace"]
            f0 = trace[0]["best_fitness"]
            fT = trace[-1]["best_fitness"]
            # First generation at which the incumbent last improved.
            last_gain = max((t["generation"] for t in trace
                             if t["best_fitness"] < fT - 1e-12), default=0)
            chrom = res.diagnostics["best_chromosome"]
            print(json.dumps({
                "dataset": slug, "method": name, "run": run + 1, "seed": seed,
                "k": k, "n": int(len(X)), "d": int(X.shape[1]),
                "observed_classes": meta["observed_classes"],
                "fitness_gen0": f0, "fitness_final": fT,
                "rel_gain": (f0 - fT) / max(abs(f0), 1e-12),
                "stalled": bool(fT >= f0 - 1e-12),
                "last_improved_generation": int(last_gain),
                "a": chrom[-4], "b": chrom[-3], "w": chrom[-2], "eta": chrom[-1],
                "runtime_seconds": elapsed,
                "evaluations": res.diagnostics["fitness_evaluations"],
                **quality(y, labels),
            }), flush=True)
