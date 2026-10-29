"""One results entry point; keep raw experiments together without changing their data."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
ARCHIVE = "LUU_TRU"
PAGE = "00_XEM_KET_QUA.html"
MAIN_DATASETS = {"iris", "flame", "jain", "wine", "glass", "ecoli",
                 "compound", "seed", "breast_tissue", "aggregation"}

def tree_digest(folder):
    digest = hashlib.sha256()
    count = 0
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        relative = path.relative_to(folder).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        count += 1
    return {"files": count, "sha256_tree": digest.hexdigest()}

def organize_existing(results=RESULTS):
    """Move only direct experiment folders, after checking both resolved paths."""
    results = Path(results).resolve()
    results.mkdir(parents=True, exist_ok=True)
    archive = results / ARCHIVE
    if archive.is_symlink() or (hasattr(archive, "is_junction") and archive.is_junction()):
        raise ValueError("Archive must be a real directory inside results.")
    archive.mkdir(exist_ok=True)
    if archive.resolve().parent != results:
        raise ValueError("Archive resolves outside results.")
    candidates = sorted(p for p in results.iterdir() if p.is_dir() and p.name != ARCHIVE)
    for source in candidates:
        target = archive / source.name
        if source.is_symlink() or (hasattr(source, "is_junction") and source.is_junction()):
            raise ValueError(f"Refusing to move a linked directory: {source}")
        if source.resolve().parent != results or target.resolve().parent != archive.resolve():
            raise ValueError("Move target is outside the intended results directory.")
        if target.exists():
            raise FileExistsError(f"Archive target already exists: {target}")
    moved = []
    for source in candidates:
        before = tree_digest(source)
        target = archive / source.name
        source.rename(target)
        after = tree_digest(target)
        if before != after:
            raise RuntimeError(f"Integrity check failed after moving {target}")
        moved.append({"from": source.name, "to": f"{ARCHIVE}/{source.name}", **after})
    if moved:
        manifest = archive / "_sap_xep.json"
        history = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else []
        history.append({"utc": datetime.now(timezone.utc).isoformat(), "moved": moved})
        manifest.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return moved

def read_summary(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row["runs"] = int(row["runs"])
        for key in list(row):
            if key.endswith(("_mean", "_std")):
                row[key] = float(row[key]) if row[key] not in ("", "None") else None
    return rows

def relative_url(path, base):
    return quote(os.path.relpath(path, base).replace("\\", "/"), safe="/")

def describe_experiment(folder, base):
    folder, base = Path(folder), Path(base)
    exp = json.loads((folder/"experiment.json").read_text(encoding="utf-8"))
    complete = bool(exp.get("completed")) and (folder/"summary.csv").exists()
    summary = read_summary(folder/"summary.csv") if complete else []
    datasets = list(dict.fromkeys(r["dataset"] for r in summary))
    methods = list(dict.fromkeys(r["method"] for r in summary))
    cfg = exp["config"]
    full = (complete and set(datasets)==MAIN_DATASETS and len(methods)==9 and int(cfg["runs"])>=30)
    files = {name:relative_url(folder/name,base) for name in (
        "index.html","report.html","summary.csv","runs.csv","extremes_comparison.csv",
        "kmeans_selection.json","experiment.json","selected_config.json","paper_differences.csv",
        "gaussian_protocol.json","degradation_vs_clean.csv","nc_l_ari.csv","ari_by_dataset.csv","wilcoxon.csv") if (folder/name).exists()}
    protocol = []
    if (folder/"nc_l_ari.csv").exists():
        with (folder/"nc_l_ari.csv").open(encoding="utf-8-sig",newline="") as stream:
            protocol=list(csv.DictReader(stream))
    return {
        "ariProtocol":protocol,
        "id":relative_url(folder,base),"name":folder.name,
        "created":exp.get("created_utc",""),"complete":complete,"full":full,
        "datasets":datasets,"methods":methods,"repeats":int(cfg["runs"]),
        "actualRuns":exp.get("n_actual_runs",0),"profile":cfg.get("profile",""),
        "fitness":cfg.get("fitness",""),"unimplemented":exp.get("unimplemented",[]),
        "summary":summary,"assets":{q.stem:relative_url(q,base) for q in folder.glob("*.png")},
        "files":files,"kind":exp.get("kind","paper"),"gaussian":exp.get("gaussian",{})}

def collect_experiments(results):
    candidates = [q for q in results.iterdir() if q.is_dir() and q.name!=ARCHIVE]
    archive = results/ARCHIVE
    if archive.exists():
        candidates.extend(q for q in archive.iterdir() if q.is_dir())
    experiments = [describe_experiment(q,results) for q in sorted(candidates) if (q/"experiment.json").exists()]
    return sorted(experiments,key=lambda e:(e["created"],e["name"]),reverse=True)

def write_single_report(folder):
    folder = Path(folder).resolve()
    experiment = describe_experiment(folder,folder)
    payload = {"experiments":[experiment],"primary":experiment["id"],"newest":experiment["id"]}
    serialized = json.dumps(payload,ensure_ascii=False).replace("<", chr(92)+"u003c")
    template = (ROOT/"templates/results_portal.html").read_text(encoding="utf-8-sig")
    (folder/"index.html").write_text(template.replace("__RESULTS_DATA__",serialized),encoding="utf-8")
    return folder/"index.html"

def publish_results(results=RESULTS):
    results = Path(results).resolve()
    results.mkdir(parents=True, exist_ok=True)
    experiments = collect_experiments(results)
    completed = [e for e in experiments if e["complete"]]
    if not completed:
        raise ValueError("No completed experiment is available to display.")
    full = [e for e in completed if e["full"]]
    primary = (full or completed)[0]
    payload = {"experiments": experiments, "primary": primary["id"],
               "newest": completed[0]["id"], "generated": datetime.now(timezone.utc).isoformat()}
    # Escape '<' so experiment strings cannot terminate the embedded JSON script.
    serialized = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    template = (ROOT / "templates" / "results_portal.html").read_text(encoding="utf-8-sig")
    (results / PAGE).write_text(template.replace("__RESULTS_DATA__", serialized), encoding="utf-8")
    folder = results / unquote(primary["id"])
    for source, target in (
        ("all_models_heatmap.png", "01_TONG_QUAN_10_BO.png"),
        ("kmeans_extremes_comparison.png", "02_SO_SANH_2_BO_KMEANS.png"),
    ):
        if (folder / source).exists():
            shutil.copy2(folder / source, results / target)
    return results / PAGE

def run_stage(stage="all", argv=None):
    """Use the existing numerical runner; only choose output and refresh the portal."""
    from common.runner import main
    argv = list(sys.argv[1:] if argv is None else argv)
    has_output = any(a == "--output" or a.startswith("--output=") for a in argv)
    if not has_output and "--list" not in argv:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        argv += ["--output", str(RESULTS / ARCHIVE / f"{stage}_{stamp}")]
    status = main(stage, argv)
    if status == 0 and "--list" not in argv and "--no-visuals" not in argv:
        print(f"MO KET QUA: {publish_results()}", flush=True)
    return status

def main():
    parser = argparse.ArgumentParser(description="Organize existing runs and rebuild the visual results entry point.")
    parser.add_argument("--organize", action="store_true", help="Move direct result folders into LUU_TRU, preserving every file.")
    args = parser.parse_args()
    if args.organize:
        for item in organize_existing():
            print(f"Archived {item['from']} -> {item['to']} ({item['files']} files, verified)")
    print(f"MO KET QUA: {publish_results()}")

if __name__ == "__main__":
    main()
