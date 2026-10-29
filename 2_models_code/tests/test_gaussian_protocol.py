"""Independent checks for synthetic contamination and the Nc/L ARI aggregation."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gaussian_data import make_study,make_replicate,score_fit
from gaussian_summary import protocol_tables,signed_rank

class GaussianProtocolTests(unittest.TestCase):
    def test_nested_outliers_balance_and_reproducibility(self):
        study=make_study()
        for data_index in (0,3,6):
            a=make_replicate(study,data_index)
            b=make_replicate(study,data_index)
            self.assertEqual(a["X_clean"].shape,(500,5))
            np.testing.assert_array_equal(a["X_clean"],b["X_clean"])
            previous=set()
            for c in study["conditions"]:
                slug=c["slug"];y=a["y_"+slug];mask=y<0
                self.assertEqual(mask.sum(),c["n_outliers"])
                current=set(np.flatnonzero(mask))
                self.assertTrue(previous.issubset(current));previous=current
                self.assertEqual(set(y[y>=0]),{0,1})
                if mask.any():
                    distance=np.linalg.norm(a["X_raw_"+slug][mask,None,:]-a["true_centers"][None,:,:],axis=2).min(axis=1)
                    self.assertTrue((distance>=4).all())
                np.testing.assert_array_equal(a["X_raw_"+slug][~mask],a["X_clean"][~mask])
                self.assertTrue(np.isfinite(a["X_scaled_"+slug]).all())
        self.assertFalse(np.array_equal(make_replicate(study,0)["X_clean"],make_replicate(study,1)["X_clean"]))

    def test_outliers_excluded_from_primary_scores(self):
        truth=np.array([0,0,1,1,-1,-1])
        centers=np.array([[0.,0.],[1.,1.]])
        one=score_fit(truth,np.array([0,0,1,1,0,0]),centers,centers)
        two=score_fit(truth,np.array([0,0,1,1,1,1]),centers,centers)
        for metric in ("accuracy_purity","ari","nmi"):
            self.assertEqual(one[metric],1.)
            self.assertEqual(one[metric],two[metric])
        self.assertEqual(one["center_rmse"],0.)

    def test_mean_best_and_exact_paired_test(self):
        study=make_study(rates=(0.,))
        study.update(runs_per_dataset=2,n_datasets=9)
        rows=[]
        slug=study["conditions"][0]["slug"]
        for d in range(1,10):
            for run in (1,2):
                for method in ("K-means","DP-GA-PFCM"):
                    value=(.3 if method=="K-means" else .6)+d*.01+run*.02
                    rows.append(dict(dataset=slug,method=method,dataset_id=d,run=run,ari=value,balance_level="test"))
        with tempfile.TemporaryDirectory() as tmp:
            table=protocol_tables(Path(tmp),rows,study,["K-means","DP-GA-PFCM"])
        main=next(r for r in table if r["method"]=="DP-GA-PFCM")
        self.assertAlmostEqual(main["ari_mean"],.68)
        self.assertAlmostEqual(main["ari_best_mean"],.69)
        self.assertEqual(main["n_total_runs"],18)
        self.assertAlmostEqual(main["wilcoxon_p"],2/512)
        self.assertEqual(main["s_marker"],"s")
        self.assertEqual(signed_rank(np.ones(9),np.ones(9)),1.)

    def test_invalid_noise_levels_rejected(self):
        for rates in ((.1,), (0.,1.), (0.,float("nan")), (0.,.05,.05)):
            with self.assertRaises(ValueError):
                make_study(rates=rates)

if __name__=="__main__":
    unittest.main()
