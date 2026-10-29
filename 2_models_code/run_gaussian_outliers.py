"""Evaluate existing clustering methods on paired Gaussian mixtures with outliers."""
import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from common.registry import METHODS, fit_method
from common.reporting import aggregate, write_csv, print_summary
from common.runner import validate_config
from gaussian_data import make_study, make_replicate, seed_for, score_fit

ROOT = Path(__file__).resolve().parent
AVAILABLE = [name for name, (_, _, available) in METHODS.items() if available]
UNAVAILABLE = [name for name, (_, _, available) in METHODS.items() if not available]

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

def worker(dataset_index, run_index, cfg, study, methods, output_text):
    output = Path(output_text)
    data_path = output/"data"/f"dataset_{dataset_index+1:03d}.npz"
    with np.load(data_path) as source:
        arrays = {name:source[name] for name in source.files}
    data_sha = hashlib.sha256(data_path.read_bytes()).hexdigest()
    fit_seed = seed_for(study["seed"], dataset_index*100000+run_index, 3)
    balance = study["balance_levels"][dataset_index//study["datasets_per_balance"]]
    balance_label = "/".join(f"{100*w:g}" for w in balance)
    rows = []
    with threadpool_limits(limits=cfg["threads"]):
        for condition in study["conditions"]:
            slug = condition["slug"]
            X, y = arrays["X_scaled_"+slug], arrays["y_"+slug]
            for method in methods:
                started = time.perf_counter()
                result = fit_method(method, X, study["Nc"], np.random.default_rng(fit_seed), copy.deepcopy(cfg))
                elapsed = time.perf_counter()-started
                labels = result.labels(cfg["hard_labels"])
                if not np.isfinite(result.centers).all() or not np.isfinite(result.membership).all():
                    raise FloatingPointError(f"{slug}/{method}: non-finite result.")
                if result.typicality is not None and not np.isfinite(result.typicality).all():
                    raise FloatingPointError(f"{slug}/{method}: non-finite typicality.")
                centers_raw = result.centers*arrays["span_"+slug]+arrays["min_"+slug]
                scores = score_fit(y, labels, centers_raw, arrays["true_centers"])
                relative = Path("artifacts")/slug/method/f"dataset_{dataset_index+1:03d}"/f"run_{run_index+1:03d}"
                artifact = output/relative
                artifact.mkdir(parents=True, exist_ok=True)
                saved = {"centers": result.centers, "centers_raw": centers_raw,
                         "membership": result.membership, "labels": labels}
                if result.typicality is not None:
                    saved["typicality"] = result.typicality
                np.savez_compressed(artifact/"model.npz", **saved)
                write_json(artifact/"details.json", {
                    "seed": fit_seed, "data_seed": seed_for(study["seed"], dataset_index, 1),
                    "outlier_seed": seed_for(study["seed"], dataset_index, 2),
                    "params": result.params, "objective": result.objective,
                    "iterations": result.iterations, "trace": result.trace,
                    "diagnostics": result.diagnostics, "metrics_scope": study["metrics_scope"]})
                rows.append({"dataset": slug, "method": method, "group": METHODS[method][0],
                    "run": run_index+1, "dataset_id":dataset_index+1, "balance_level":balance_label, "seed": fit_seed,
                    "data_seed": seed_for(study["seed"], dataset_index, 1),
                    "outlier_seed": seed_for(study["seed"], dataset_index, 2),
                    "k": study["Nc"], **scores, "outlier_ratio": condition["actual_ratio"],
                    "n_inliers": condition["n_inliers"], "n_outliers": condition["n_outliers"],
                    "runtime_seconds": elapsed, "objective": result.objective,
                    "iterations": result.iterations,
                    "fitness_evaluations": result.diagnostics.get("fitness_evaluations", 0),
                    "artifact": relative.as_posix(), "data_artifact": data_path.relative_to(output).as_posix(),
                    "data_sha256": data_sha})
    write_json(output/"replicates"/f"dataset_{dataset_index+1:03d}_run_{run_index+1:03d}.json", rows)
    return rows

def summarize(output, rows, study, methods):
    names = [c["slug"] for c in study["conditions"]]
    summary, ranks = aggregate(rows, names, methods)
    for record in summary:
        subset = [r for r in rows if r["dataset"]==record["dataset"] and r["method"]==record["method"]]
        values = np.array([r["center_rmse"] for r in subset])
        record["center_rmse_mean"] = float(values.mean())
        record["center_rmse_std"] = float(values.std(ddof=1)) if len(values)>1 else None
        record["outlier_ratio"] = subset[0]["outlier_ratio"]
        record["n_inliers"] = subset[0]["n_inliers"]
        record["n_outliers"] = subset[0]["n_outliers"]
    write_csv(output/"summary.csv", summary)
    write_csv(output/"rank_sums.csv", ranks)
    control = next(c["slug"] for c in study["conditions"] if c["n_outliers"]==0)
    lookup = {(r["dataset"], r["method"], r["dataset_id"], r["run"]): r for r in rows}
    changes = []
    for record in summary:
        subset = [r for r in rows if r["dataset"]==record["dataset"] and r["method"]==record["method"]]
        row = {"dataset": record["dataset"], "method": record["method"], "outlier_ratio": record["outlier_ratio"]}
        for metric in ("accuracy_purity", "ari", "nmi", "center_rmse"):
            deltas = np.array([r[metric]-lookup[(control, r["method"], r["dataset_id"], r["run"])][metric] for r in subset])
            row[metric+"_delta_vs_clean_mean"] = float(deltas.mean())
            row[metric+"_delta_vs_clean_std"] = float(deltas.std(ddof=1)) if len(deltas)>1 else None
        changes.append(row)
    write_csv(output/"degradation_vs_clean.csv", changes)
    from gaussian_summary import protocol_tables
    protocol_tables(output, rows, study, methods)
    return summary, ranks

def main():
    try:
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nc", "--Nc", type=int, default=2)
    parser.add_argument("--features", "--L", type=int, default=5)
    parser.add_argument("--samples", type=int, default=500)
    parser.add_argument("--outlier-rates", nargs="+", type=float, default=[0., .05, .1, .2])
    parser.add_argument("--runs", type=int, default=25)
    parser.add_argument("--datasets-per-balance", type=int, default=3)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1))
    parser.add_argument("--methods", nargs="+", choices=AVAILABLE, default=AVAILABLE)
    parser.add_argument("--config", type=Path, default=ROOT/"configs/corrected_reference.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--quick", action="store_true", help="One dataset per balance, two restarts, population=8, generations=5; smoke only.")
    args = parser.parse_args()
    if not 1 <= args.jobs <= (os.cpu_count() or 1) or args.runs < 1 or args.datasets_per_balance < 1 or args.seed < 0:
        parser.error("Positive jobs/runs and nonnegative seed required.")
    if len(set(args.methods)) != len(args.methods):
        parser.error("Methods must be distinct.")
    try:
        study = make_study(args.nc, args.features, args.samples, args.outlier_rates, args.seed)
    except ValueError as error:
        parser.error(str(error))
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    cfg["runs"] = 2 if args.quick else args.runs
    cfg["profile"] = "gaussian_outliers_quick_smoke" if args.quick else "gaussian_outliers_reference_fitness"
    if args.quick:
        cfg.update(population=8, generations=5)
    validate_config(cfg)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = (args.output or ROOT/"results"/"LUU_TRU"/f"gaussian_nc{args.nc}_l{args.features}_{stamp}").resolve()
    if output.exists() and any(output.iterdir()):
        parser.error(f"Output exists and is nonempty: {output}")
    for subdir in ("data", "artifacts", "replicates"):
        (output/subdir).mkdir(parents=True, exist_ok=True)
    study["datasets_per_balance"] = 1 if args.quick else args.datasets_per_balance
    study["n_datasets"] = 3*study["datasets_per_balance"]
    study["runs_per_dataset"] = cfg["runs"]
    study["replicates"] = study["n_datasets"]
    study["summary_mean"] = "Mean and sample SD across all dataset x algorithm-run ARI values."
    study["summary_best"] = "For each dataset take maximum ARI over algorithm runs; report mean and sample SD over dataset maxima. Label-informed retrospective benchmark statistic, not a deployable model-selection rule."
    study["wilcoxon"] = "K-means vs DP-GA-PFCM on paired dataset mean ARI (one pair per dataset), two-sided alpha=.05; exact sign permutations with ties; four planned outlier conditions, no multiplicity adjustment. Round differences to 12 decimals only for the test."
    for dataset_index in range(study["n_datasets"]):
        np.savez_compressed(output/"data"/f"dataset_{dataset_index+1:03d}.npz", **make_replicate(study,dataset_index))
    write_json(output/"gaussian_protocol.json", study)
    write_json(output/"selected_config.json", cfg)
    sources = [p for p in ROOT.rglob("*.py") if not any(part in (".venv", "datasets", "results", "__pycache__") for part in p.relative_to(ROOT).parts)]
    experiment = {
        "created_utc": datetime.now(timezone.utc).isoformat(), "stage": "synthetic",
        "kind": "gaussian_outliers", "gaussian": study, "config": cfg, "completed": False,
        "methods": args.methods, "unimplemented": UNAVAILABLE, "command": sys.argv,
        "datasets": [{"slug": c["slug"], "n_samples": args.samples, "n_features": args.features,
                      "true_k": args.nc, **c} for c in study["conditions"]],
        "n_actual_runs": 0, "parallel_replicate_jobs": args.jobs,
        "source_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "environment": {"python": sys.version, "platform": platform.platform(),
            "packages": {name: importlib.metadata.version(name) for name in
                         ("numpy", "scipy", "scikit-learn", "threadpoolctl", "matplotlib")}},
        "timing": "Wall fit time includes DPC; concurrent workers may contend for CPU.",
        "evaluation": study["metrics_scope"],
        "comparison_scope": "Independent synthetic experiment; not published paper results."}
    write_json(output/"experiment.json", experiment)
    print(f"Nc={args.nc}, L={args.features}, n={args.samples}; {len(study['conditions'])} outlier levels x "
          f"{study['n_datasets']} datasets x {cfg['runs']} restarts x {len(args.methods)} methods; jobs={args.jobs}", flush=True)
    rows = []
    try:
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            futures = {pool.submit(worker, d, r, cfg, study, args.methods, str(output)): (d,r)
                       for d in range(study["n_datasets"]) for r in range(cfg["runs"])}
            done=0
            for future in as_completed(futures):
                rows.extend(future.result())
                done+=1
                rows.sort(key=lambda r:(r["dataset"],r["dataset_id"],r["run"],args.methods.index(r["method"])))
                write_csv(output/"runs.csv",rows)
                experiment["n_actual_runs"]=len(rows)
                write_json(output/"experiment.json",experiment)
                print(f"Completed {done}/{study['n_datasets']*cfg['runs']} dataset/restart tasks | {len(rows)} fits saved",flush=True)
        expected=len(study["conditions"])*study["n_datasets"]*cfg["runs"]*len(args.methods)
        if len(rows)!=expected:
            raise RuntimeError(f"Expected {expected} fits, found {len(rows)}")
        summary, ranks = summarize(output, rows, study, args.methods)
        from gaussian_figures import build_gaussian_figures
        experiment["visual_results"] = build_gaussian_figures(output, summary, rows, experiment)
        experiment["completed"] = True
        write_json(output/"experiment.json", experiment)
        from result_portal import write_single_report, publish_results
        write_single_report(output)
        publish_results()
        print_summary(summary, ranks)
        print("GAUSSIAN REPORT:", output/"index.html", flush=True)
        print("Central report: code/results/00_XEM_KET_QUA.html -> Luot moi nhat", flush=True)
    except Exception as error:
        experiment["completed"] = False
        experiment["error"] = f"{type(error).__name__}: {error}"
        write_json(output/"experiment.json", experiment)
        raise

if __name__ == "__main__":
    main()
