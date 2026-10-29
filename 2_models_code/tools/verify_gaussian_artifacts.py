"""Audit Gaussian predictions, inlier scoring and Nc/L Mean/Best/Wilcoxon tables."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from gaussian_data import score_fit,seed_for
from gaussian_summary import signed_rank

def read(path):
    with path.open(encoding="utf-8-sig",newline="") as stream:
        return list(csv.DictReader(stream))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("folder",type=Path)
    parser.add_argument("--current-sources",action="store_true")
    args=parser.parse_args()
    folder=args.folder.resolve()
    exp=json.loads((folder/"experiment.json").read_text(encoding="utf-8"))
    assert exp["completed"]
    study=exp["gaussian"];methods=exp["methods"]
    rows=read(folder/"runs.csv")
    assert len(rows)==study["n_datasets"]*study["runs_per_dataset"]*len(study["conditions"])*len(methods)==exp["n_actual_runs"]
    cache={};seen=set()
    for row in rows:
        key=(row["dataset"],row["method"],int(row["dataset_id"]),int(row["run"]))
        assert key not in seen,key
        seen.add(key)
        relative=row["data_artifact"]
        if relative not in cache:
            p=folder/relative
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            with np.load(p) as data:
                arrays={name:data[name] for name in data.files}
            cache[relative]=(digest,arrays)
        digest,arrays=cache[relative]
        assert digest==row["data_sha256"]
        slug=row["dataset"];truth=arrays["y_"+slug]
        assert arrays["X_raw_"+slug].shape==(study["n_samples"],study["L"])
        assert int((truth<0).sum())==int(row["n_outliers"])
        assert len(np.unique(truth[truth>=0]))==study["Nc"]
        assert int(row["seed"])==seed_for(study["seed"],(int(row["dataset_id"])-1)*100000+int(row["run"])-1,3)
        with np.load(folder/row["artifact"]/"model.npz") as model:
            assert np.isfinite(model["membership"]).all()
            np.testing.assert_allclose(model["membership"].sum(axis=1),1.,atol=1e-12)
            labels=np.argmax(model["typicality"] if exp["config"]["hard_labels"]=="typicality" else model["membership"],axis=1)
            np.testing.assert_array_equal(labels,model["labels"])
            np.testing.assert_allclose(model["centers_raw"],model["centers"]*arrays["span_"+slug]+arrays["min_"+slug])
            actual=score_fit(truth,model["labels"],model["centers_raw"],arrays["true_centers"])
        for metric,value in actual.items():
            assert abs(value-float(row[metric]))<1e-12,(key,metric)
    assert len(cache)==study["n_datasets"]
    table=read(folder/"nc_l_ari.csv")
    assert len(table)==len(methods)*len(study["conditions"])
    dataset_means={}
    for record in table:
        condition=next(c for c in study["conditions"] if abs(float(record["outlier_ratio"])-c["actual_ratio"])<1e-12)
        subset=[r for r in rows if r["dataset"]==condition["slug"] and r["method"]==record["method"]]
        values=[float(r["ari"]) for r in subset]
        best=[];means=[]
        for d in range(1,study["n_datasets"]+1):
            block=[float(r["ari"]) for r in subset if int(r["dataset_id"])==d]
            assert len(block)==study["runs_per_dataset"]
            best.append(max(block));means.append(float(np.mean(block)))
        dataset_means[(condition["slug"],record["method"])]=means
        for column,expected in (("ari_mean",np.mean(values)),("ari_std",np.std(values,ddof=1)),
                                ("ari_best_mean",np.mean(best)),("ari_best_std",np.std(best,ddof=1))):
            assert abs(float(record[column])-expected)<1e-12,(record["method"],column)
    for test in read(folder/"wilcoxon.csv"):
        condition=next(c for c in study["conditions"] if abs(float(test["outlier_ratio"])-c["actual_ratio"])<1e-12)
        p=signed_rank(dataset_means[(condition["slug"],"K-means")],dataset_means[(condition["slug"],"DP-GA-PFCM")])
        assert abs(p-float(test["p_value"]))<1e-12
        assert int(test["n_pairs"])==study["n_datasets"]
    if args.current_sources:
        for name,sha in exp["source_sha256"].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
    print(json.dumps({"status":"PASS","Nc":study["Nc"],"L":study["L"],"datasets":len(cache),
                      "runs_per_dataset":study["runs_per_dataset"],"fits":len(rows),
                      "mean_best_rows":len(table),"outlier_levels":[c["actual_ratio"] for c in study["conditions"]]}))
if __name__=="__main__":
    main()
