"""Read ONLY feature_columns. Labels are inaccessible to optimizers."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np

def get_default_dataset_root():
    code_parent = Path(__file__).resolve().parents[1]
    project_root = Path(__file__).resolve().parents[2]
    for c in [project_root / "1_datasets", project_root / "datasets", code_parent / "datasets", code_parent / "1_datasets"]:
        if c.exists() and any(c.glob("*/*/metadata.json")):
            return c
    return code_parent / "datasets"

DEFAULT_ROOT = get_default_dataset_root()

def load_dataset(slug, root=None):
    if root is None:
        root = DEFAULT_ROOT
    matches = list(Path(root).glob("*/"+slug+"/metadata.json"))
    if len(matches) != 1:
        for alt in [Path(__file__).resolve().parents[2] / "1_datasets", Path(__file__).resolve().parents[1] / "datasets"]:
            if alt.exists():
                m = list(Path(alt).glob("*/" + slug + "/metadata.json"))
                if len(m) == 1:
                    matches = m
                    break
    if len(matches) != 1:
        raise ValueError(f"Dataset '{slug}' absent or ambiguous. Run download_datasets.py.")
    folder = matches[0].parent
    meta = json.loads(matches[0].read_text(encoding="utf-8"))
    path = folder/"data.csv"
    if hashlib.sha256(path.read_bytes()).hexdigest() != meta["data_sha256"]:
        raise ValueError(f"{slug}: data.csv checksum mismatch.")
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    X = np.array([[float(row[col]) for col in meta["feature_columns"]] for row in rows])
    y = np.array([int(row[meta["label_column"]]) for row in rows])
    if X.shape != (meta["n_samples"], meta["n_features"]) or not np.isfinite(X).all():
        raise ValueError(f"{slug}: invalid shape or non-finite data.")
    low, high = X.min(axis=0), X.max(axis=0)
    span = high-low
    constant = span == 0
    scaled = (X-low)/np.where(constant, 1.0, span)
    meta["scaling"] = {"min": low.tolist(), "max": high.tolist(),
                       "constant_columns": [meta["feature_columns"][i] for i in np.flatnonzero(constant)]}
    return scaled, y, meta

def dataset_names(group, root=None):
    if root is None:
        root = DEFAULT_ROOT
    names = []
    for path in Path(root).glob("*/metadata.json"):  # retained for custom layouts
        pass
    for path in Path(root).glob("*/*/metadata.json"):
        meta = json.loads(path.read_text(encoding="utf-8"))
        if group == "all" or meta["group"] == group or (group == "su_dung" and meta.get("group") in ["su_dung", "10_datasets_bai_bao"]):
            names.append((meta["table1_order"], meta["slug"]))
    return [name for _, name in sorted(names)]
