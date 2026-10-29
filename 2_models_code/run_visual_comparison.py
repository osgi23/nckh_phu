"""Run the ten primary datasets at Table 5 budget and make one shared dashboard."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from threadpoolctl import threadpool_info
from common.data import dataset_names
from common.registry import METHODS
from common.reporting import aggregate, paper_differences, report_html, write_csv, print_summary
from common.statistics import METRICS, tests

ROOT=Path(__file__).resolve().parent
AVAILABLE=[name for name,(_,_,available) in METHODS.items() if available]
UNAVAILABLE=[name for name,(_,_,available) in METHODS.items() if not available]

def load_csv(path):
    with path.open(encoding="utf-8-sig",newline="") as stream:
        return list(csv.DictReader(stream))

def typed_row(row):
    for key in ("run","seed","k","observed_clusters","iterations","fitness_evaluations"):
        row[key]=int(row[key])
    for key in (*METRICS,"accuracy_hungarian","runtime_seconds","objective"):
        row[key]=float(row[key])
    return row

def child_worker(dataset, output, config):
    child=output/"datasets"/dataset
    experiment=child/"experiment.json"
    if experiment.exists():
        manifest=json.loads(experiment.read_text(encoding="utf-8"))
        if manifest.get("completed") and manifest.get("config")==config:
            return dataset,"reused"
        raise RuntimeError(f"{dataset}: existing incomplete or different config; use a new output folder.")
    cmd=[sys.executable,"-u",str(ROOT/"run_compare_all.py"),
         "--config",str((output/"selected_config.json").resolve()),
         "--datasets",dataset,"--methods",*AVAILABLE,
         "--output",str(child.resolve()),"--no-visuals","--color","never"]
    log=output/"logs"/(dataset+".log")
    with log.open("w",encoding="utf-8") as stream:
        result=subprocess.run(cmd,cwd=str(ROOT.parent),stdout=stream,stderr=subprocess.STDOUT,creationflags=getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0),
                              env={**os.environ,"MPLCONFIGDIR":str((ROOT.parent/"tmp"/"matplotlib_cache").resolve())})
    if result.returncode:
        tail=log.read_text(encoding="utf-8",errors="replace")[-3000:]
        raise RuntimeError(f"{dataset}: exit {result.returncode}; see {log}\n{tail}")
    manifest=json.loads(experiment.read_text(encoding="utf-8"))
    if not manifest.get("completed"): raise RuntimeError(f"{dataset}: run did not complete.")
    return dataset,"completed"

def combine(output, datasets, config, jobs):
    rows=[]; metadata=[]
    source_hashes=None
    for dataset in datasets:
        child=output/"datasets"/dataset
        exp=json.loads((child/"experiment.json").read_text(encoding="utf-8"))
        if not exp["completed"] or exp["methods"]!=AVAILABLE or exp["config"]!=config:
            raise ValueError(f"Experiment is incomplete or inconsistent: {dataset}")
        if source_hashes is None: source_hashes=exp["source_sha256"]
        elif exp["source_sha256"]!=source_hashes:
            raise ValueError("Sources changed between dataset runs; cannot merge.")
        metadata.extend(exp["datasets"])
        for row in load_csv(child/"runs.csv"):
            row=typed_row(row)
            row["artifact"]=(Path("datasets")/dataset/row["artifact"]).as_posix()
            rows.append(row)
    expected=len(datasets)*len(AVAILABLE)*config["runs"]
    if len(rows)!=expected: raise ValueError(f"Expected {expected} runs; found {len(rows)}")
    write_csv(output/"runs.csv",rows)
    summary,ranks=aggregate(rows,datasets,AVAILABLE)
    references,differences=paper_differences(summary,ROOT)
    omnibus,pairwise=tests(rows,AVAILABLE,datasets,config["statistical_alpha"])
    write_csv(output/"summary.csv",summary)
    write_csv(output/"rank_sums.csv",ranks)
    write_csv(output/"paper_differences.csv",differences)
    write_csv(output/"kruskal_wallis.csv",omnibus)
    write_csv(output/"dunn_bonferroni.csv",pairwise,
              ("dataset","metric","first","second","p_bonferroni"))
    experiment={
        "created_utc":datetime.now(timezone.utc).isoformat(),"stage":"all","config":config,
        "command":sys.argv,"methods":AVAILABLE,"unimplemented":UNAVAILABLE,
        "datasets":metadata,"completed":False,"n_actual_runs":len(rows),
        "parallel_dataset_jobs":jobs,
        "environment":{"python":sys.version,"platform":platform.platform(),"machine":platform.machine(),
                       "packages":{name:importlib.metadata.version(name) for name in
                                   ("numpy","scipy","scikit-learn","threadpoolctl","matplotlib")},
                       "threadpools":threadpool_info()},
        "source_sha256":source_hashes,
        "data_root":str((ROOT/"datasets").resolve()),
        "comparison_scope":"Actual methods only; published means are reference data, not runs.",
        "timing":"wall time full fit per dataset worker; concurrent jobs may contend for CPU resources",
        "selection_rule":"Two extrema are chosen AFTER all K-means runs, using its mean purity on the 10 primary datasets.",
    }
    report_html(output/"report.html",summary,ranks,references,differences,experiment)
    os.environ.setdefault("MPLCONFIGDIR",str((ROOT.parent/"tmp"/"matplotlib_cache").resolve()))
    from common.visual_results import build_visual_results
    experiment["visual_results"]=build_visual_results(output,summary,rows,experiment)
    experiment["completed"]=True
    (output/"experiment.json").write_text(json.dumps(experiment,ensure_ascii=False,indent=2),encoding="utf-8")
    print_summary(summary,ranks,color=False)
    selection=json.loads((output/"kmeans_selection.json").read_text(encoding="utf-8"))
    print("K-means selected:",[(r["role"],r["dataset"],round(r["accuracy_purity_mean"],4))
                               for r in selection["selected"]],flush=True)
    print("Dashboard:",(output/"index.html").resolve(),flush=True)
    print("Actual runs:",len(rows),flush=True)

def main():
    parser=argparse.ArgumentParser(description="Run all 10 primary datasets and compare the K-means extremes.")
    parser.add_argument("--config",type=Path,default=ROOT/"configs"/"corrected_reference.json")
    parser.add_argument("--output",type=Path,
                        default=ROOT/"results"/"LUU_TRU"/f"visual_main10_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    parser.add_argument("--jobs",type=int,default=4)
    parser.add_argument("--runs",type=int)
    parser.add_argument("--resume",action="store_true")
    args=parser.parse_args()
    if not 1<=args.jobs<=min(os.cpu_count() or 1,10):
        parser.error("--jobs must be between 1 and available dataset/CPU capacity.")
    cfg=json.loads(args.config.read_text(encoding="utf-8"))
    if args.runs is not None: cfg["runs"]=args.runs
    from common.runner import validate_config
    validate_config(cfg)
    output=args.output.resolve()
    if output.exists() and any(output.iterdir()) and not args.resume:
        parser.error("Output exists and is nonempty; choose a new folder or --resume.")
    output.mkdir(parents=True,exist_ok=True)
    (output/"logs").mkdir(exist_ok=True)
    (output/"datasets").mkdir(exist_ok=True)
    selected_config=output/"selected_config.json"
    if selected_config.exists():
        if json.loads(selected_config.read_text(encoding="utf-8"))!=cfg:
            parser.error("Existing selected_config.json differs from request.")
    else:
        selected_config.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding="utf-8")
    datasets=dataset_names("su_dung")
    print(f"Running {len(datasets)} datasets x {len(AVAILABLE)} methods x {cfg['runs']} repeats = "
          f"{len(datasets)*len(AVAILABLE)*cfg['runs']} runs; jobs={args.jobs}",flush=True)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures=[pool.submit(child_worker,d,output,cfg) for d in datasets]
        for future in as_completed(futures):
            dataset,status=future.result()
            print(f"[{dataset}] {status}",flush=True)
    combine(output,datasets,cfg,args.jobs)
    from result_portal import publish_results
    print("MO KET QUA:", publish_results(), flush=True)

if __name__=="__main__":
    main()
