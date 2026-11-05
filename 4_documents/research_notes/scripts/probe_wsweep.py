"""Does the fuzzifier region explain the gap? DPC centers + PFCM at fixed w.
No search at all, so this isolates the parameter region from the optimizer."""
import copy,json,sys
from pathlib import Path
import numpy as np
CODE=Path("/home/user/nckh_phu/2_models_code"); sys.path.insert(0,str(CODE))
from common.data import load_dataset
from common.density_peak import density_peak_centers
from common.metrics import quality
from common.numerics import solve_pfcm
from gaussian_data import make_study,make_replicate,condition_slug
BASE=json.loads((CODE/"configs"/"corrected_reference.json").read_text())
WS=[1.1,1.2,1.5,2.0,3.0,5.0]
def run(tag,X,y,k):
    anchors,_=density_peak_centers(X,k,BASE)
    out={"dataset":tag,"k":k}
    for w in WS:
        cfg=dict(BASE,a=1.0,b=1.0,w=w,eta=2.0)
        res=solve_pfcm(X,anchors.copy(),cfg)
        lab=res.labels(BASE["hard_labels"])
        q=quality(y,lab)
        out[f"ari_w{w}"]=round(q["ari"],4); out[f"clus_w{w}"]=q["observed_clusters"]
    print(json.dumps(out),flush=True)
for slug in ["pima","rice","wifi"]:
    X,y,meta=load_dataset(slug); run(slug,X,y,meta["paper_k"])
CLEAN=condition_slug(0.0)
for nc,dims,sep in [(3,2,1.5),(3,2,2.5),(4,5,2.0),(4,5,3.0)]:
    st=make_study(nc=nc,dimensions=dims,samples=500,rates=(0.0,),seed=2026); st["center_separation"]=sep
    a=make_replicate(st,0); run(f"gauss_nc{nc}_L{dims}_sep{sep}",a["X_scaled_"+CLEAN],a["y_"+CLEAN],nc)
