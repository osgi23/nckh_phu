"""Can a LABEL-FREE criterion pick the right fuzzifier region per dataset?

The w-sweep showed swings up to +0.51 ARI between fuzzifier settings, and the
best w differs per dataset. If an internal index applied to the CONVERGED
solution ranks those settings like ARI does, then multi-start + label-free
selection captures that swing without ever touching labels.

Reports, per dataset: ARI of the setting each criterion picks, versus the best
and worst settings available. Oracle column is for reference only.
"""
import json,sys
from pathlib import Path
import numpy as np
CODE=Path("/home/user/nckh_phu/2_models_code"); sys.path.insert(0,str(CODE))
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from common.data import load_dataset
from common.density_peak import density_peak_centers
from common.metrics import quality
from common.numerics import solve_pfcm
from gaussian_data import make_study,make_replicate,condition_slug
BASE=json.loads((CODE/"configs"/"corrected_reference.json").read_text())
WS=[1.1,1.2,1.5,2.0,3.0,5.0]
CLEAN=condition_slug(0.0)

def evaluate(tag,X,y,k):
    anchors,_=density_peak_centers(X,k,BASE)
    rows=[]
    for w in WS:
        res=solve_pfcm(X,anchors.copy(),dict(BASE,a=1.,b=1.,w=w,eta=2.))
        lab=res.labels(BASE["hard_labels"]); nu=len(np.unique(lab))
        row={"w":w,"ari":quality(y,lab)["ari"],"clusters":nu}
        if nu<2:
            row.update(ch=-np.inf,db=np.inf,sil=-np.inf)
        else:
            row.update(ch=float(calinski_harabasz_score(X,lab)),
                       db=float(davies_bouldin_score(X,lab)),
                       sil=float(silhouette_score(X,lab)))
        rows.append(row)
    aris=[r["ari"] for r in rows]
    pick=lambda key,sign: rows[int(np.argmax([sign*r[key] for r in rows]))]["ari"]
    return {"dataset":tag,"k":k,
            "ari_w2_default":round(rows[WS.index(2.0)]["ari"],4),
            "ari_pick_ch":round(pick("ch",1),4),
            "ari_pick_db":round(pick("db",-1),4),
            "ari_pick_sil":round(pick("sil",1),4),
            "ari_best_oracle":round(max(aris),4),
            "ari_worst":round(min(aris),4)}

out=[]
for slug in ["pima","rice","wifi"]:
    X,y,meta=load_dataset(slug); out.append(evaluate(slug,X,y,meta["paper_k"]))
for nc,dims,sep in [(3,2,1.5),(3,2,2.5),(4,5,2.0),(4,5,3.0),(6,2,2.0),(8,2,2.0),(8,5,3.0)]:
    st_=make_study(nc=nc,dimensions=dims,samples=500,rates=(0.,),seed=2026); st_["center_separation"]=sep
    a=make_replicate(st_,0); out.append(evaluate(f"gauss_nc{nc}_L{dims}_sep{sep}",a["X_scaled_"+CLEAN],a["y_"+CLEAN],nc))
hdr=f"{'dataset':<24}{'k':>2}{'w=2 mac dinh':>14}{'chon theo CH':>14}{'chon theo DB':>14}{'chon theo Sil':>15}{'oracle':>9}{'te nhat':>9}"
print(hdr)
import statistics as stt
for r in out:
    print(f"{r['dataset']:<24}{r['k']:>2}{r['ari_w2_default']:>14.4f}{r['ari_pick_ch']:>14.4f}{r['ari_pick_db']:>14.4f}{r['ari_pick_sil']:>15.4f}{r['ari_best_oracle']:>9.4f}{r['ari_worst']:>9.4f}")
print(f"{'TRUNG BINH':<26}"+''.join(f"{stt.mean(r[k] for r in out):>14.4f}" for k in ("ari_w2_default","ari_pick_ch","ari_pick_db"))+f"{stt.mean(r['ari_pick_sil'] for r in out):>15.4f}{stt.mean(r['ari_best_oracle'] for r in out):>9.4f}{stt.mean(r['ari_worst'] for r in out):>9.4f}")
