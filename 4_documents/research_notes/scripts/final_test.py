"""FINAL confirmation on the 10 paper benchmarks, 30 seeds, three methods paired.

  ga_baseline : DP-GA-PFCM exactly as reproduced
  ga_wpinned  : label-free fuzzifier selection (resampling stability among
                settings that realise k clusters), then DP-GA-PFCM with w
                pinned there, so the optimiser spends its budget on the
                centres and on a, b, eta
  wsweep_only : the cheap method - the same selection with no GA at all

No labels are used by any method. Reported once.
"""
import copy,json,sys,time
from pathlib import Path
import numpy as np
CODE=Path("/home/user/nckh_phu/2_models_code"); sys.path.insert(0,str(CODE))
from common.data import load_dataset, dataset_names
from common.density_peak import density_peak_centers
from common.metrics import quality
from common.numerics import solve_pfcm
from common.consensus import select_fuzzifier, pin_fuzzifier
from common.registry import fit_method
BASE=json.loads((CODE/"configs"/"corrected_reference.json").read_text())
BASE["population"]=80; BASE["generations"]=100
RUNS=int(sys.argv[1]) if len(sys.argv)>1 else 30
for slug in dataset_names("su_dung"):
    X,y,meta=load_dataset(slug); k=meta["paper_k"]
    for run in range(RUNS):
        seed=int(np.random.SeedSequence([BASE["seed"],meta["table1_order"],run]).generate_state(1)[0])
        rec={"dataset":slug,"run":run+1,"seed":seed,"k":k,"n":int(len(X))}

        t=time.perf_counter()
        r0=fit_method("DP-GA-PFCM",X,k,np.random.default_rng(seed),copy.deepcopy(BASE))
        q0=quality(y,r0.labels(BASE["hard_labels"]))
        rec.update({"base_ari":q0["ari"],"base_purity":q0["accuracy_purity"],"base_nmi":q0["nmi"],
                    "base_clusters":q0["observed_clusters"],"base_seconds":time.perf_counter()-t})

        t=time.perf_counter()
        w,info=select_fuzzifier(X,k,copy.deepcopy(BASE),np.random.default_rng(seed))
        cfg=pin_fuzzifier(copy.deepcopy(BASE),w)
        r1=fit_method("DP-GA-PFCM",X,k,np.random.default_rng(seed),copy.deepcopy(cfg))
        q1=quality(y,r1.labels(BASE["hard_labels"]))
        rec.update({"pin_ari":q1["ari"],"pin_purity":q1["accuracy_purity"],"pin_nmi":q1["nmi"],
                    "pin_clusters":q1["observed_clusters"],"pin_seconds":time.perf_counter()-t,
                    "w_selected":w,"w_fell_back":info["fell_back"]})

        t=time.perf_counter()
        anchors,_=density_peak_centers(X,k,BASE)
        lab=solve_pfcm(X,anchors.copy(),dict(BASE,a=1.,b=1.,w=w,eta=2.)).labels(BASE["hard_labels"])
        q2=quality(y,lab)
        rec.update({"sweep_ari":q2["ari"],"sweep_purity":q2["accuracy_purity"],"sweep_nmi":q2["nmi"],
                    "sweep_clusters":q2["observed_clusters"],"sweep_seconds":time.perf_counter()-t})
        print(json.dumps(rec),flush=True)
