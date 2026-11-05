"""Stability selection: pick the fuzzifier whose partition is most reproducible
under resampling. Uses no labels. Labels appear only in the reported ARI.

For each w: draw B subsamples at 80%, cluster each, and average the ARI between
every pair of partitions restricted to the points both subsamples contain.
"""
import json,sys,itertools
from pathlib import Path
import numpy as np
CODE=Path("/home/user/nckh_phu/2_models_code"); sys.path.insert(0,str(CODE))
from sklearn.metrics import adjusted_rand_score
from common.data import load_dataset
from common.density_peak import density_peak_centers
from common.metrics import quality
from common.numerics import solve_pfcm
from gaussian_data import make_study,make_replicate,condition_slug
BASE=json.loads((CODE/"configs"/"corrected_reference.json").read_text())
WS=[1.1,1.2,1.5,2.0,3.0,5.0]; B=8; FRAC=0.8; CLEAN=condition_slug(0.0)

def fit_w(X,k,w):
    anchors,_=density_peak_centers(X,k,BASE)
    res=solve_pfcm(X,anchors.copy(),dict(BASE,a=1.,b=1.,w=w,eta=2.))
    return res.labels(BASE["hard_labels"])

def evaluate(tag,X,y,k):
    rng=np.random.default_rng(4242); n=len(X); m=int(FRAC*n)
    subs=[np.sort(rng.choice(n,m,replace=False)) for _ in range(B)]
    stab,full=[],[]
    for w in WS:
        parts=[]
        for idx in subs:
            lab=fit_w(X[idx],k,w)
            mp=np.full(n,-1); mp[idx]=lab; parts.append(mp)
        sc=[]
        for a,b in itertools.combinations(range(B),2):
            both=(parts[a]>=0)&(parts[b]>=0)
            if both.sum()>k: sc.append(adjusted_rand_score(parts[a][both],parts[b][both]))
        stab.append(float(np.mean(sc)) if sc else -np.inf)
        full.append(quality(y,fit_w(X,k,w))["ari"])
    j=int(np.argmax(stab))
    return {"dataset":tag,"k":k,"w_chosen":WS[j],"ari_stability":round(full[j],4),
            "ari_w2":round(full[WS.index(2.0)],4),"ari_oracle":round(max(full),4),
            "stab_profile":[round(s,3) for s in stab]}

out=[]
for slug in ["pima","rice","wifi"]:
    X,y,meta=load_dataset(slug); out.append(evaluate(slug,X,y,meta["paper_k"]))
for nc,dims,sep in [(3,2,1.5),(3,2,2.5),(4,5,2.0),(4,5,3.0),(6,2,2.0),(8,2,2.0),(8,5,3.0)]:
    s_=make_study(nc=nc,dimensions=dims,samples=500,rates=(0.,),seed=2026); s_["center_separation"]=sep
    a=make_replicate(s_,0); out.append(evaluate(f"gauss_nc{nc}_L{dims}_sep{sep}",a["X_scaled_"+CLEAN],a["y_"+CLEAN],nc))
import statistics as st
print(f"{'dataset':<24}{'k':>2}{'w chon':>8}{'ARI on dinh':>13}{'ARI w=2':>10}{'oracle':>9}")
for r in out:
    print(f"{r['dataset']:<24}{r['k']:>2}{r['w_chosen']:>8}{r['ari_stability']:>13.4f}{r['ari_w2']:>10.4f}{r['ari_oracle']:>9.4f}")
print(f"{'TRUNG BINH':<34}{st.mean(r['ari_stability'] for r in out):>13.4f}{st.mean(r['ari_w2'] for r in out):>10.4f}{st.mean(r['ari_oracle'] for r in out):>9.4f}")
