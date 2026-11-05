"""Ceiling of the GA stage: best ARI reachable in a 400-chromosome sample of the
search space, versus the ARI the fitness actually selects. Synthetic dev sets."""
import copy,json,sys
from pathlib import Path
import numpy as np
CODE=Path("/home/user/nckh_phu/2_models_code"); sys.path.insert(0,str(CODE))
from common.density_peak import density_peak_centers
from common.meta_pfcm import PFCMSearch
from common.metrics import quality
from common.numerics import solve_pfcm
from gaussian_data import make_study,make_replicate,condition_slug
BASE=json.loads((CODE/"configs"/"corrected_reference.json").read_text()); BASE["population"]=400
CLEAN=condition_slug(0.0)
for nc,dims,sep in [(3,2,1.5),(3,2,2.5),(4,5,2.0),(4,5,3.0)]:
    st=make_study(nc=nc,dimensions=dims,samples=500,rates=(0.0,),seed=2026); st["center_separation"]=sep
    arr=make_replicate(st,0); X,y=arr["X_scaled_"+CLEAN],arr["y_"+CLEAN]
    anchors,dpc=density_peak_centers(X,nc,BASE)
    p=PFCMSearch(X,nc,copy.deepcopy(BASE))
    genes=p.initial(anchors,np.random.default_rng(777),dpc.get("candidates"))
    _,sur=p.evaluate(genes)
    aris=[]
    for g in genes:
        c,par=p.decode(g); r=solve_pfcm(X,c,dict(BASE,**par))
        aris.append(quality(y,r.labels(BASE["hard_labels"]))["ari"])
    aris=np.array(aris)
    print(json.dumps({"dataset":f"gauss_nc{nc}_L{dims}_sep{sep}","n_sampled":len(genes),
      "ari_selected_by_fitness":round(float(aris[int(np.argmin(sur))]),4),
      "ari_max_in_space":round(float(aris.max()),4),
      "ari_mean":round(float(aris.mean()),4),
      "headroom":round(float(aris.max()-aris[int(np.argmin(sur))]),4)}),flush=True)
