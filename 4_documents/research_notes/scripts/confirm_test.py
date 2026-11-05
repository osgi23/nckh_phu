"""CONFIRMATION on the 10 paper benchmarks. Reported once, not used to select.

Compares the baseline DP-GA-PFCM against a cheap alternative: sweep 6 fuzzifier
values from the same DPC centres, then pick one by resampling stability
restricted to solutions that realise k clusters. No labels anywhere in either
method. Also records cost in PFCM solves and seconds.
"""
import copy,json,sys,itertools,time
from pathlib import Path
import numpy as np
CODE=Path("/home/user/nckh_phu/2_models_code"); sys.path.insert(0,str(CODE))
from sklearn.metrics import adjusted_rand_score
from common.data import load_dataset, dataset_names
from common.density_peak import density_peak_centers
from common.metrics import quality
from common.numerics import solve_pfcm
from common.registry import fit_method
BASE=json.loads((CODE/"configs"/"corrected_reference.json").read_text())
BASE["population"]=80; BASE["generations"]=100
WS=[1.1,1.2,1.5,2.0,3.0,5.0]; B=8; FRAC=.8; RUNS=5

def cheap(X,k,seed):
    rng=np.random.default_rng(seed); n=len(X); m=int(FRAC*n)
    subs=[np.sort(rng.choice(n,m,replace=False)) for _ in range(B)]
    solves=0; rows=[]
    for w in WS:
        anchors,_=density_peak_centers(X,k,BASE)
        lab=solve_pfcm(X,anchors.copy(),dict(BASE,a=1.,b=1.,w=w,eta=2.)).labels(BASE["hard_labels"]); solves+=1
        parts=[]
        for idx in subs:
            a2,_=density_peak_centers(X[idx],k,BASE)
            l=solve_pfcm(X[idx],a2.copy(),dict(BASE,a=1.,b=1.,w=w,eta=2.)).labels(BASE["hard_labels"]); solves+=1
            mp=np.full(n,-1); mp[idx]=l; parts.append(mp)
        sc=[]
        for i,j in itertools.combinations(range(B),2):
            bo=(parts[i]>=0)&(parts[j]>=0)
            if bo.sum()>k: sc.append(adjusted_rand_score(parts[i][bo],parts[j][bo]))
        rows.append({"w":w,"labels":lab,"clusters":len(np.unique(lab)),
                     "stab":float(np.mean(sc)) if sc else -np.inf})
    pool=[r for r in rows if r["clusters"]==k] or rows
    pick=pool[int(np.argmax([r["stab"] for r in pool]))]
    return pick["labels"],solves,pick["w"]

for slug in dataset_names("su_dung"):
    X,y,meta=load_dataset(slug); k=meta["paper_k"]
    for run in range(RUNS):
        seed=int(np.random.SeedSequence([BASE["seed"],meta["table1_order"],run]).generate_state(1)[0])
        t=time.perf_counter()
        res=fit_method("DP-GA-PFCM",X,k,np.random.default_rng(seed),copy.deepcopy(BASE))
        tg=time.perf_counter()-t
        qg=quality(y,res.labels(BASE["hard_labels"]))
        t=time.perf_counter(); lab,solves,wsel=cheap(X,k,seed); tc=time.perf_counter()-t
        qc=quality(y,lab)
        print(json.dumps({"dataset":slug,"run":run+1,"seed":seed,"k":k,
          "ga_ari":qg["ari"],"ga_purity":qg["accuracy_purity"],"ga_clusters":qg["observed_clusters"],
          "ga_seconds":tg,"ga_pfcm_evaluations":res.diagnostics["fitness_evaluations"],
          "cheap_ari":qc["ari"],"cheap_purity":qc["accuracy_purity"],"cheap_clusters":qc["observed_clusters"],
          "cheap_seconds":tc,"cheap_pfcm_solves":solves,"cheap_w":wsel}),flush=True)
