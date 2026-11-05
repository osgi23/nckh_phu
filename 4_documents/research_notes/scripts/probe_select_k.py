"""Same label-free selection, but restricted to solutions that actually yield k
clusters. k is given in this problem setting, so requiring the partition to
realise k clusters uses no labels. Every criterion tested so far failed by
preferring merged partitions; this removes exactly that escape route."""
import json,sys,itertools
from pathlib import Path
import numpy as np
CODE=Path("/home/user/nckh_phu/2_models_code"); sys.path.insert(0,str(CODE))
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score
from common.data import load_dataset
from common.density_peak import density_peak_centers
from common.metrics import quality
from common.numerics import solve_pfcm
from gaussian_data import make_study,make_replicate,condition_slug
BASE=json.loads((CODE/"configs"/"corrected_reference.json").read_text())
WS=[1.1,1.2,1.5,2.0,3.0,5.0]; B=8; FRAC=.8; CLEAN=condition_slug(0.)
def fit_w(X,k,w):
    a,_=density_peak_centers(X,k,BASE)
    return solve_pfcm(X,a.copy(),dict(BASE,a=1.,b=1.,w=w,eta=2.)).labels(BASE["hard_labels"])
def evaluate(tag,X,y,k):
    rng=np.random.default_rng(4242); n=len(X); m=int(FRAC*n)
    subs=[np.sort(rng.choice(n,m,replace=False)) for _ in range(B)]
    rows=[]
    for w in WS:
        lab=fit_w(X,k,w); nu=len(np.unique(lab))
        parts=[]
        for idx in subs:
            l=fit_w(X[idx],k,w); mp=np.full(n,-1); mp[idx]=l; parts.append(mp)
        sc=[adjusted_rand_score(parts[a][(parts[a]>=0)&(parts[b]>=0)],parts[b][(parts[a]>=0)&(parts[b]>=0)])
            for a,b in itertools.combinations(range(B),2)]
        rows.append({"w":w,"ari":quality(y,lab)["ari"],"clusters":nu,
                     "stab":float(np.mean(sc)) if sc else -np.inf,
                     "ch":float(calinski_harabasz_score(X,lab)) if nu>1 else -np.inf})
    full=[r for r in rows if r["clusters"]==k] or rows
    best=lambda pool,key: pool[int(np.argmax([r[key] for r in pool]))]["ari"]
    return {"dataset":tag,"k":k,"ari_w2":rows[WS.index(2.)]["ari"],
            "stab_free":best(rows,"stab"),"stab_kfull":best(full,"stab"),
            "ch_free":best(rows,"ch"),"ch_kfull":best(full,"ch"),
            "oracle":max(r["ari"] for r in rows),"n_kfull":len(full),
            "clusters":[r["clusters"] for r in rows]}
out=[]
for slug in ["pima","rice","wifi"]:
    X,y,meta=load_dataset(slug); out.append(evaluate(slug,X,y,meta["paper_k"]))
for nc,dims,sep in [(3,2,1.5),(3,2,2.5),(4,5,2.0),(4,5,3.0),(6,2,2.0),(8,2,2.0),(8,5,3.0)]:
    s_=make_study(nc=nc,dimensions=dims,samples=500,rates=(0.,),seed=2026); s_["center_separation"]=sep
    a=make_replicate(s_,0); out.append(evaluate(f"gauss_nc{nc}_L{dims}_sep{sep}",a["X_scaled_"+CLEAN],a["y_"+CLEAN],nc))
import statistics as st
print(f"{'dataset':<24}{'k':>2}{'w=2':>8}{'stab':>8}{'stab|k':>8}{'CH':>8}{'CH|k':>8}{'oracle':>8}  so cum theo w")
for r in out:
    print(f"{r['dataset']:<24}{r['k']:>2}{r['ari_w2']:>8.4f}{r['stab_free']:>8.4f}{r['stab_kfull']:>8.4f}{r['ch_free']:>8.4f}{r['ch_kfull']:>8.4f}{r['oracle']:>8.4f}  {r['clusters']}")
print(f"{'TRUNG BINH':<26}"+''.join(f"{st.mean(r[k] for r in out):>8.4f}" for k in ("ari_w2","stab_free","stab_kfull","ch_free","ch_kfull","oracle")))
