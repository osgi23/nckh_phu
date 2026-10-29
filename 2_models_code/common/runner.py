"""CLI shared by all three groups. Labels are used ONLY after fit."""
import argparse
import copy
import hashlib
import importlib.metadata
import json
import platform
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits, threadpool_info
from common.data import load_dataset, dataset_names, DEFAULT_ROOT
from common.registry import METHODS, STAGES, fit_method
from common.reporting import write_csv, aggregate, print_summary, report_html, paper_differences
from common.statistics import tests
ROOT = Path(__file__).resolve().parents[1]

def validate_config(cfg):
    numeric = ("a", "b", "w", "eta", "gamma_scale", "tol", "seed_jitter",
               "mutation_range", "crossover_rate", "mutation_rate", "dc_quantile",
               "pso_inertia_start", "pso_inertia_end", "pso_c1", "pso_c2",
               "pso_velocity_fraction", "sca_amplitude", "statistical_alpha")
    for key in numeric:
        if isinstance(cfg[key], bool) or not isinstance(cfg[key], (int, float)) or not np.isfinite(cfg[key]):
            raise ValueError(f"{key} must be a finite number.")
    for key in ("seed", "elite_count", "mutation_precision"):
        if isinstance(cfg[key], bool) or not isinstance(cfg[key], int):
            raise ValueError(f"{key} must be an integer.")
    if not 0 < cfg["statistical_alpha"] < 1:
        raise ValueError("statistical_alpha must be in (0,1).")
    for key in ("pso_c1", "pso_c2", "pso_velocity_fraction", "sca_amplitude"):
        if cfg[key] <= 0:
            raise ValueError(f"{key} must be > 0.")
    for key in ("pso_inertia_start", "pso_inertia_end"):
        if cfg[key] < 0:
            raise ValueError(f"{key} must be >= 0.")
    ref_w = cfg.get("fitness_reference_w", 2.0)
    if isinstance(ref_w, bool) or not isinstance(ref_w, (int, float)) or not np.isfinite(ref_w) or ref_w <= 1:
        raise ValueError("fitness_reference_w must be finite and > 1.")
    if cfg.get("stop_criterion", "objective") not in ("objective", "centers"):
        raise ValueError("stop_criterion must be objective or centers.")
    if cfg.get("stop_mode", "absolute") not in ("absolute", "relative"):
        raise ValueError("stop_mode must be absolute or relative.")
    for key in ("runs","max_iter","population","generations","dpc_block_size","dc_sample_pairs","threads","dc_exact_limit"):
        if isinstance(cfg[key],bool) or not isinstance(cfg[key],int) or cfg[key]<1:
            raise ValueError(f"{key} must be a positive integer.")
    if cfg["population"]<4:
        raise ValueError("population >= 4 required for FBI peer sampling.")
    for key in ("crossover_rate","mutation_rate","dc_quantile"):
        if not 0<=cfg[key]<=1:
            raise ValueError(f"{key} must be in [0,1].")
    if cfg["dc_quantile"]==0:
        raise ValueError("dc_quantile must be > 0.")
    if not isinstance(cfg["elite_count"],int) or not 0<=cfg["elite_count"]<cfg["population"]:
        raise ValueError("elite_count must be an integer >=0 and < population.")
    if cfg["a"]<=0 or cfg["b"]<=0 or cfg["w"]<=1 or cfg["eta"]<=1:
        raise ValueError("a,b > 0 and w,eta > 1 required.")
    if cfg["gamma_scale"]<=0 or cfg["tol"]<0:
        raise ValueError("gamma_scale > 0 and tol >= 0 required.")
    if cfg["seed"]<0 or cfg["seed_jitter"]<0 or cfg["mutation_range"]<0:
        raise ValueError("seed, seed_jitter, mutation_range must be >= 0.")
    if not 4<=cfg["mutation_precision"]<=20:
        raise ValueError("mutation_precision in [4,20].")
    for key in ("a","b","w","eta"):
        bound=cfg["parameter_bounds"][key]
        if (not isinstance(bound, list) or len(bound)!=2
                or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not np.isfinite(v) for v in bound)
                or bound[0]>=bound[1] or bound[0]<=(1 if key in ("w","eta") else 0)):
            raise ValueError(f"Invalid search bounds for {key}: {bound}")
        if not bound[0]<=cfg[key]<=bound[1]:
            raise ValueError(f"Initial {key} outside bounds.")
    if cfg["gamma_refresh"] not in ("each_step","fixed"):
        raise ValueError("gamma_refresh: each_step or fixed.")
    if cfg["fitness"] not in ("fcm","pfcm","sse","fcm_reference"):
        raise ValueError("fitness: fcm, pfcm, sse or fcm_reference.")
    if cfg["k_policy"] not in ("paper","observed"):
        raise ValueError("k_policy: paper or observed.")
    if cfg["hard_labels"] not in ("membership","typicality"):
        raise ValueError("hard_labels: membership or typicality.")

def main(stage="all", argv=None):
    parser=argparse.ArgumentParser(description="DP-GA-PFCM reproduction: actual quality and paper comparison.")
    parser.add_argument("--config",type=Path,default=ROOT/"configs"/"corrected_reference.json")
    parser.add_argument("--profile",choices=("paper","quick"),default="paper")
    parser.add_argument("--group",choices=("su_dung","khong_su_dung","all"),default="su_dung")
    parser.add_argument("--datasets",nargs="+",help="Dataset slugs, e.g. iris flame jain")
    parser.add_argument("--methods",nargs="+",choices=list(METHODS))
    for option in ("runs","population","generations","max-iter","seed"):
        parser.add_argument("--"+option,type=int)
    parser.add_argument("--fitness",choices=("fcm","pfcm","sse","fcm_reference"))
    parser.add_argument("--mutation-rate",type=float)
    parser.add_argument("--k-policy",choices=("paper","observed"))
    parser.add_argument("--set",action="append",default=[],metavar="KEY=JSON",
                        help="Override config; nested keys use dots.")
    parser.add_argument("--data-root",type=Path,default=DEFAULT_ROOT)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--color",choices=("auto","always","never"),default="auto")
    parser.add_argument("--list",action="store_true")
    parser.add_argument("--require-all",action="store_true",help="Stop if a requested baseline has no implementation.")
    parser.add_argument("--no-visuals",action="store_true",help="Internal: skip per-dataset figures when an aggregate dashboard will be generated.")
    args=parser.parse_args(argv)
    requested=args.methods or STAGES[stage]
    if args.list:
        for name in requested:
            group,module,available=METHODS[name]
            print(f"{group:6} {name:16} {'implemented_with_assumptions' if available else 'MISSING_SOURCE'} {module.replace('.', '/')}.py")
        return 0
    missing=[name for name in requested if not METHODS[name][2]]
    if missing:
        print("NOT IMPLEMENTED (excluded from actual rankings): "+", ".join(missing),flush=True)
    methods=[name for name in requested if METHODS[name][2]]
    if (missing and (args.require_all or args.methods)) or not methods:
        parser.error("Missing source for requested baseline(s). See ASSUMPTIONS.md. No substitute is executed.")
    cfg=json.loads(args.config.read_text(encoding="utf-8"))
    if args.profile=="quick":
        cfg.update(profile="quick_smoke_not_paper_budget",runs=2,population=12,generations=8,max_iter=100)
    for key in ("runs","population","generations","max_iter","seed","fitness","mutation_rate","k_policy"):
        value=getattr(args,key)
        if value is not None:
            cfg[key]=value
    for override in args.set:
        try:
            key,value=override.split("=",1)
            target=cfg
            parts=key.split(".")
            for part in parts[:-1]:
                target=target[part]
            if parts[-1] not in target:
                raise ValueError(f"Unknown key {key}")
            target[parts[-1]]=json.loads(value)
        except (ValueError,KeyError,TypeError) as error:
            parser.error(f"Invalid --set {override}: {error}")
    try:
        validate_config(cfg)
    except (ValueError,KeyError,TypeError) as error:
        parser.error(str(error))
    if cfg["fitness"] in ("fcm", "pfcm"):
        print("NOTE: raw fitness varies with gene parameters; this is the literal/alternative paper interpretation.",flush=True)
    selected=args.datasets or dataset_names(args.group,args.data_root)
    if not selected or len(set(selected))!=len(selected):
        parser.error("Datasets must be nonempty and distinct.")
    if len(set(methods))!=len(methods):
        parser.error("Methods must be distinct.")
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output=args.output or ROOT/"results"/f"{stage}_{args.profile}_{stamp}"
    if output.exists() and any(output.iterdir()):
        parser.error(f"Output folder is not empty: {output}")
    output.mkdir(parents=True,exist_ok=True)
    experiment={"created_utc":datetime.now(timezone.utc).isoformat(),"stage":stage,"config":cfg,
        "command":sys.argv,"methods":methods,"unimplemented":missing,"datasets":[],"completed":False,
        "environment":{"python":sys.version,"platform":platform.platform(),"machine":platform.machine(),
            "processor":platform.processor(),"packages":{name:importlib.metadata.version(name) for name in
                                                       ("numpy","scipy","scikit-learn","threadpoolctl","matplotlib")}},
        "timing":"wall time full fit including DPC; excluding CSV/scaling/metrics/report",
        "comparison_scope":"Actual methods only; published means are reference data, not runs.",
        "data_root":str(args.data_root.resolve())}
    sources=sorted(p for p in ROOT.rglob("*.py") if ".venv" not in p.parts and "datasets" not in p.parts)
    experiment["source_sha256"]={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    exp_path=output/"experiment.json"
    def save_experiment():
        exp_path.write_text(json.dumps(experiment,ensure_ascii=False,indent=2),encoding="utf-8")
    save_experiment()
    rows=[]
    color=args.color=="always" or (args.color=="auto" and sys.stdout.isatty())
    from common.metrics import quality
    try:
        with threadpool_limits(limits=cfg["threads"]):
            experiment["environment"]["threadpools"]=threadpool_info()
            for slug in selected:
                X,y,meta=load_dataset(slug,args.data_root)
                k=meta["paper_k"] if cfg["k_policy"]=="paper" else meta["observed_classes"]
                if k>len(np.unique(X,axis=0)):
                    raise ValueError(f"{slug}: k exceeds unique observations.")
                experiment["datasets"].append(meta)
                for run in range(cfg["runs"]):
                    seed=int(np.random.SeedSequence([cfg["seed"],meta["table1_order"],run]).generate_state(1)[0])
                    for name in methods:
                        print(f"[{slug}] run {run+1}/{cfg['runs']} | {name} | seed={seed}",flush=True)
                        started=time.perf_counter()
                        result=fit_method(name,X,k,np.random.default_rng(seed),copy.deepcopy(cfg))
                        elapsed=time.perf_counter()-started
                        labels=result.labels(cfg["hard_labels"])
                        if not np.isfinite(result.centers).all() or not np.isfinite(result.membership).all():
                            raise FloatingPointError(f"{slug}/{name}: non-finite output.")
                        if result.typicality is not None and not np.isfinite(result.typicality).all():
                            raise FloatingPointError(f"{slug}/{name}: non-finite typicality.")
                        score=quality(y,labels)
                        artifact=output/"artifacts"/slug/name/f"run_{run+1:03}"
                        artifact.mkdir(parents=True,exist_ok=True)
                        arrays={"centers":result.centers,"membership":result.membership,"labels":labels}
                        if result.typicality is not None:
                            arrays["typicality"]=result.typicality
                        np.savez_compressed(artifact/"model.npz",**arrays)
                        details={"seed":seed,"params":result.params,"objective":result.objective,
                            "iterations":result.iterations,"trace":result.trace,"diagnostics":result.diagnostics}
                        (artifact/"details.json").write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding="utf-8")
                        rows.append({"dataset":slug,"method":name,"group":METHODS[name][0],"run":run+1,"seed":seed,
                            "k":k,**score,"runtime_seconds":elapsed,"objective":result.objective,
                            "iterations":result.iterations,"fitness_evaluations":result.diagnostics.get("fitness_evaluations",0),
                            "artifact":str(artifact.relative_to(output))})
                        write_csv(output/"runs.csv",rows)
                save_experiment()
    except Exception as error:
        experiment["error"]=f"{type(error).__name__}: {error}"
        save_experiment()
        raise
    summary,ranks=aggregate(rows,selected,methods)
    references,differences=paper_differences(summary,ROOT)
    omnibus,pairwise=tests(rows,methods,selected,cfg["statistical_alpha"])
    write_csv(output/"summary.csv",summary)
    write_csv(output/"rank_sums.csv",ranks)
    write_csv(output/"paper_differences.csv",differences)
    write_csv(output/"kruskal_wallis.csv",omnibus)
    write_csv(output/"dunn_bonferroni.csv",pairwise,("dataset","metric","first","second","p_bonferroni"))
    experiment["n_actual_runs"]=len(rows)
    report_html(output/"report.html",summary,ranks,references,differences,experiment)
    if not args.no_visuals:
        os.environ.setdefault("MPLCONFIGDIR",str((ROOT.parent/"tmp"/"matplotlib_cache").resolve()))
        from common.visual_results import build_visual_results
        experiment["visual_results"] = build_visual_results(output, summary, rows, experiment)
    experiment["completed"]=True
    save_experiment()
    print_summary(summary,ranks,color)
    print(f"\nSaved actual results: {output.resolve()}\nColored report: {(output/'report.html').resolve()}")
    return 0
