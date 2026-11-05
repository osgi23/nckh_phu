import json,sys,copy,time
from pathlib import Path
import numpy as np
CODE=Path("/home/user/nckh_phu/2_models_code"); sys.path.insert(0,str(CODE))
from common.data import load_dataset,dataset_names
from common.metrics import quality
from common.registry import fit_method
BASE=json.loads((CODE/"configs"/"corrected_reference.json").read_text())
BASE["population"]=80; BASE["generations"]=100
VARIANTS={"baseline":{}, "lamarckian":{"lamarckian":True}}
for slug in dataset_names(sys.argv[1] if len(sys.argv)>1 else "khong_su_dung"):
    X,y,meta=load_dataset(slug)
    k=meta["paper_k"] if BASE["k_policy"]=="paper" else meta["observed_classes"]
    for run in range(5):
        seed=int(np.random.SeedSequence([BASE["seed"],meta["table1_order"],run]).generate_state(1)[0])
        for vname,over in VARIANTS.items():
            cfg=dict(BASE,**over)
            t=time.perf_counter()
            res=fit_method("DP-GA-PFCM",X,k,np.random.default_rng(seed),copy.deepcopy(cfg))
            el=time.perf_counter()-t
            tr=res.diagnostics["optimizer_trace"]; f0=tr[0]["best_fitness"]; fT=tr[-1]["best_fitness"]
            print(json.dumps({"dataset":slug,"variant":vname,"run":run+1,"seed":seed,"k":k,
              "n":int(len(X)),"fitness_gen0":f0,"fitness_final":fT,
              "rel_gain":(f0-fT)/max(abs(f0),1e-12),"runtime_seconds":el,
              "w":res.diagnostics["best_chromosome"][-2],
              **quality(y,res.labels(BASE["hard_labels"]))}),flush=True)
