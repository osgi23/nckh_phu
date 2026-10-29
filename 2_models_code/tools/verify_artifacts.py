"""Recompute metrics from saved labels and verify run counts, seed and hashes."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from common.data import load_dataset
from common.metrics import quality
parser=argparse.ArgumentParser()
parser.add_argument("result_folder",type=Path)
args=parser.parse_args()
folder=args.result_folder
experiment=json.loads((folder/"experiment.json").read_text(encoding="utf-8"))
assert experiment["completed"]
with (folder/"runs.csv").open(encoding="utf-8-sig",newline="") as stream:
    rows=list(csv.DictReader(stream))
expected=len(experiment["datasets"])*len(experiment["methods"])*experiment["config"]["runs"]
assert len(rows)==expected==experiment["n_actual_runs"]
ys={meta["slug"]:load_dataset(meta["slug"])[1] for meta in experiment["datasets"]}
seen=set()
for row in rows:
    key=(row["dataset"],row["method"],row["run"])
    assert key not in seen
    seen.add(key)
    path=folder/row["artifact"]
    model=np.load(path/"model.npz")
    assert np.isfinite(model["centers"]).all()
    np.testing.assert_allclose(model["membership"].sum(axis=1),1.,atol=1e-12)
    actual=quality(ys[row["dataset"]],model["labels"])
    for metric,value in actual.items():
        assert abs(value-float(row[metric]))<1e-12,(key,metric)
    detail=json.loads((path/"details.json").read_text(encoding="utf-8"))
    assert detail["seed"]==int(row["seed"])
    if "best_chromosome" in detail["diagnostics"]:
        assert len(detail["diagnostics"]["best_chromosome"])==model["centers"].size+4
assert set(row["dataset"] for row in rows)==set(ys)
with (ROOT/"reference"/"paper_metrics.csv").open(encoding="utf-8-sig",newline="") as stream:
    refs=list(csv.DictReader(stream))
assert len(refs)==504
assert next(r for r in refs if r["table"]=="11" and r["dataset"]=="glass"
            and r["method"]=="DP-PFCM" and r["metric"]=="accuracy_purity")["mean"]=="0.066"
assert next(r for r in refs if r["table"]=="6" and r["dataset"]=="glass"
            and r["method"]=="DP-PFCM" and r["metric"]=="accuracy_purity")["mean"]=="0.566"
# Code may have gained documentation/tools since a run: check recorded numerical sources.
for name,expected_sha in experiment["source_sha256"].items():
    if name.startswith(("common/","blue_baselines/","orange_comparisons/","purple_main_model/")) or name.startswith(("common\\","blue_baselines\\","orange_comparisons\\","purple_main_model\\")):
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected_sha,name
print(f"Verified {len(rows)} actual runs, predictions/metrics/seeds/code/data; reference 504 cells.")
