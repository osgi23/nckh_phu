"""Screen consensus variants on the DEVELOPMENT suite (same suite as screen.py)."""
import copy,json,sys,time
from pathlib import Path
import numpy as np
CODE=Path("/home/user/nckh_phu/2_models_code"); sys.path.insert(0,str(CODE))
from common.data import load_dataset
from common.metrics import quality
from common.consensus import consensus_labels
from common.registry import fit_method
from gaussian_data import make_study,make_replicate,condition_slug
NAME=sys.argv[1]; OVER=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}; SEEDS=int(sys.argv[3]) if len(sys.argv)>3 else 5
BASE=json.loads((CODE/"configs"/"corrected_reference.json").read_text()); BASE["population"]=80; BASE["generations"]=100
REAL=["pima","rice","wifi"]
SYNTH=[(3,2,1.5),(3,2,2.5),(4,5,2.0),(4,5,3.0),(6,2,2.0),(8,2,2.0),(8,5,3.0)]
CLEAN=condition_slug(0.0)
def emit(tag,X,y,k,order):
    for run in range(SEEDS):
        seed=int(np.random.SeedSequence([BASE["seed"],order,run]).generate_state(1)[0])
        t=time.perf_counter()
        if NAME=="ga_baseline":
            res=fit_method("DP-GA-PFCM",X,k,np.random.default_rng(seed),copy.deepcopy(BASE))
            lab=res.labels(BASE["hard_labels"]); info={"members":0,"members_kept":0,"filter_fallback":False,"refined":False}
        else:
            lab,info=consensus_labels(X,k,copy.deepcopy(BASE),np.random.default_rng(seed),**OVER)
        el=time.perf_counter()-t
        print(json.dumps({"variant":NAME,"dataset":tag,"run":run+1,"seed":seed,"k":k,
          "n":int(len(X)),"seconds":el,**info,**quality(y,lab)}),flush=True)
for o,slug in enumerate(REAL,start=101):
    X,y,m=load_dataset(slug); emit(slug,X,y,m["paper_k"],o)
for o,(nc,d,sep) in enumerate(SYNTH,start=201):
    s=make_study(nc=nc,dimensions=d,samples=500,rates=(0.,),seed=2026); s["center_separation"]=sep
    a=make_replicate(s,0); emit(f"gauss_nc{nc}_L{d}_sep{sep}",a["X_scaled_"+CLEAN],a["y_"+CLEAN],nc,o)
