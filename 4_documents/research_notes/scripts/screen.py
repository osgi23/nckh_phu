"""Screen one algorithm variant on the DEVELOPMENT suite only.

Dev suite = 3 real dev datasets + synthetic Gaussian with controlled overlap.

Room Occupancy is excluded from screening for two reasons declared before any
variant was run: 20560 samples at ~78 s/run, and its baseline ARI is 0.017, so
it carries no signal. It returns in the confirmation pass.

The synthetic part exists because the 4 real dev datasets have no headroom:
rice 0.684 and wifi 0.856 are near their ceiling, pima 0.104 and
room_occupancy 0.017 are near the floor. A dev set that cannot move cannot
discriminate between variants. Overlap is swept via center_separation.

Usage: screen.py <variant-name> '<json-overrides>'
Writes JSONL to stdout.
"""
import copy
import json
import sys
import time
from pathlib import Path

import numpy as np

CODE = Path("/home/user/nckh_phu/2_models_code")
sys.path.insert(0, str(CODE))

from common.data import load_dataset
from common.metrics import quality
from common.registry import fit_method
from gaussian_data import make_study, make_replicate, condition_slug

NAME = sys.argv[1]
OVERRIDES = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
SEEDS = int(sys.argv[3]) if len(sys.argv) > 3 else 5

BASE = json.loads((CODE / "configs" / "corrected_reference.json").read_text())
BASE["population"] = 80
BASE["generations"] = 100

REAL_DEV = ["pima", "rice", "wifi"]
# (Nc, L, center_separation): separation 4.0 is the project's own protocol;
# smaller values make the Gaussians overlap and open up headroom.
SYNTH = [(3, 2, 1.5), (3, 2, 2.5), (4, 5, 2.0), (4, 5, 3.0),
         # High-k cases added after the first screen: the dev suite topped out
         # at k=4 while the test benchmarks reach k=6,7,8, and cluster collapse
         # is a k-dependent failure mode (Ecoli returns 4 clusters for k=8).
         # Declared before any variant was run on them.
         (6, 2, 2.0), (8, 2, 2.0), (8, 5, 3.0)]
CLEAN = condition_slug(0.0)


def synth_case(nc, dims, sep, replicate):
    study = make_study(nc=nc, dimensions=dims, samples=500, rates=(0.0,), seed=2026)
    study["center_separation"] = sep
    arrays = make_replicate(study, replicate)
    return arrays["X_scaled_" + CLEAN], arrays["y_" + CLEAN]


def emit(tag, X, y, k, order):
    for run in range(SEEDS):
        seed = int(np.random.SeedSequence([BASE["seed"], order, run]).generate_state(1)[0])
        cfg = copy.deepcopy(dict(BASE, **OVERRIDES))
        started = time.perf_counter()
        res = fit_method("DP-GA-PFCM", X, k, np.random.default_rng(seed), cfg)
        elapsed = time.perf_counter() - started
        trace = res.diagnostics["optimizer_trace"]
        f0, fT = trace[0]["best_fitness"], trace[-1]["best_fitness"]
        print(json.dumps({
            "variant": NAME, "dataset": tag, "run": run + 1, "seed": seed, "k": k,
            "n": int(len(X)), "d": int(X.shape[1]),
            "rel_gain": (f0 - fT) / max(abs(f0), 1e-12),
            "runtime_seconds": elapsed,
            "w": res.diagnostics["best_chromosome"][-2],
            **quality(y, res.labels(BASE["hard_labels"])),
        }), flush=True)


for order, slug in enumerate(REAL_DEV, start=101):
    X, y, meta = load_dataset(slug)
    emit(slug, X, y, meta["paper_k"] if BASE["k_policy"] == "paper" else meta["observed_classes"], order)

for order, (nc, dims, sep) in enumerate(SYNTH, start=201):
    X, y = synth_case(nc, dims, sep, replicate=0)
    emit(f"gauss_nc{nc}_L{dims}_sep{sep}", X, y, nc, order)
