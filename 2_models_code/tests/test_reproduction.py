"""Numerical and evaluation checks independent of reported paper scores."""
import copy
import json
import sys
import unittest
from pathlib import Path
import numpy as np
from scipy.stats import norm
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from common.data import load_dataset,dataset_names
from common.density_peak import density_peak_centers
from common.numerics import memberships,typicalities,pfcm_step,solve_fcm,solve_pfcm
from common.metrics import quality
from common.registry import METHODS,fit_method
from common.statistics import tests
from common.runner import validate_config

class ReproductionChecks(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads((ROOT/"configs"/"paper_table5.json").read_text())
        self.cfg.update(population=8,generations=3,max_iter=100)

    def test_membership_known_answer_and_zero_distance(self):
        np.testing.assert_allclose(memberships(np.array([[1.,4.]]),2),[[.8,.2]])
        np.testing.assert_allclose(memberships(np.array([[0.,0.,4.]]),2),[[.5,.5,0.]])
        with self.assertRaises(ValueError):
            memberships(np.ones((2,2)),1)

    def test_typicality_known_answer(self):
        t=typicalities(np.array([[0.,1.,3.]]),np.ones(3),1,2)
        np.testing.assert_allclose(t,[[1.,.5,.25]])

    def test_pfcm_step_known_answer(self):
        # Symmetric X: U=(.5,.5), gamma=1, T=(.5,.5), weighted mean=1.
        X=np.array([[0.],[2.]])
        centers=np.array([[1.],[1.]])
        params=dict(a=1.,b=1.,w=2.,eta=2.,gamma_scale=1.)
        new,gamma=pfcm_step(X,centers,params)
        np.testing.assert_allclose(gamma,[1.,1.])
        np.testing.assert_allclose(new,[[1.],[1.]])

    def test_purity_not_hungarian_and_permutation_invariance(self):
        y=np.array([0,0,1,1])
        split=np.array([0,1,2,3])
        score=quality(y,split)
        self.assertEqual(score["accuracy_purity"],1.)
        self.assertEqual(score["accuracy_hungarian"],.5)
        score=quality(y,np.array([9,9,3,3]))
        for metric in ("accuracy_purity","accuracy_hungarian","ari","nmi"):
            self.assertAlmostEqual(score[metric],1.)

    def test_geometric_nmi_known_entropy_answer(self):
        y=np.array([0,0,1,1])
        split=np.array([0,1,2,3])
        # MI=ln2; H(y)=ln2; H(split)=ln4 -> NMI=1/sqrt2.
        self.assertAlmostEqual(quality(y,split)["nmi"],1/np.sqrt(2))

    def test_dpc_exact_small_example_and_block_invariance(self):
        X=np.array([[0.],[1.],[3.]])
        cfg=dict(self.cfg,dc_quantile=.5,dpc_block_size=1)
        centers,info=density_peak_centers(X,2,cfg)
        self.assertEqual(info["dc"],2.)
        np.testing.assert_array_equal(centers,[[1.],[3.]])
        other,_=density_peak_centers(X,2,dict(cfg,dpc_block_size=20))
        np.testing.assert_array_equal(centers,other)

    def test_tied_density_finite_and_distinct_centers(self):
        X=np.array([[0.],[1.],[0.],[1.]])
        centers,info=density_peak_centers(X,2,self.cfg)
        self.assertTrue(np.isfinite(info["delta"]).all())
        self.assertEqual(len(np.unique(centers,axis=0)),2)

    def test_data_schema_and_user_split(self):
        self.assertEqual(len(dataset_names("su_dung")),10)
        self.assertEqual(set(dataset_names("khong_su_dung")),{"pima","room_occupancy","rice","wifi"})
        for slug in dataset_names("all"):
            X,y,meta=load_dataset(slug)
            self.assertEqual(X.shape[1],len(meta["feature_columns"]))
            self.assertNotIn("label",meta["feature_columns"])
            self.assertNotIn("label_original",meta["feature_columns"])
            self.assertGreaterEqual(X.min(),0.)
            self.assertLessEqual(X.max(),1.)
        _,_,glass=load_dataset("glass")
        self.assertEqual((glass["paper_k"],glass["observed_classes"]),(7,6))

    def test_seed_reproducibility_all_available_methods(self):
        X,_,_=load_dataset("iris")
        for name,(_,_,available) in METHODS.items():
            if not available:
                continue
            with self.subTest(method=name):
                first=fit_method(name,X,3,np.random.default_rng(42),copy.deepcopy(self.cfg))
                second=fit_method(name,X,3,np.random.default_rng(42),copy.deepcopy(self.cfg))
                np.testing.assert_array_equal(first.centers,second.centers)
                np.testing.assert_allclose(first.membership.sum(axis=1),1.)
                self.assertTrue(np.isfinite(first.objective))
                if first.typicality is not None:
                    self.assertTrue(np.all((first.typicality>=0)&(first.typicality<=1)))
                trace=first.diagnostics.get("optimizer_trace")
                if trace:
                    self.assertEqual(len(trace),self.cfg["generations"]+1)
                    self.assertTrue(np.all(np.diff([r["best_fitness"] for r in trace])<=0))

    def test_separable_clusters_and_fcm_objective(self):
        X=np.array([[0.],[.01],[.02],[.98],[.99],[1.]])
        centers=np.array([[0.],[1.]])
        for result in (solve_fcm(X,centers),solve_pfcm(X,centers,self.cfg)):
            self.assertEqual(quality([0,0,0,1,1,1],result.labels())["ari"],1.)
        fcm=solve_fcm(X,centers)
        self.assertTrue(np.all(np.diff([r["objective"] for r in fcm.trace])<=1e-10))

    def test_fitness_variants_and_fixed_gamma(self):
        X,_,_=load_dataset("iris")
        for kind in ("fcm","pfcm","sse"):
            cfg=dict(self.cfg,fitness=kind,gamma_refresh="fixed",lamarckian=True)
            result=fit_method("DP-GA-PFCM",X,3,np.random.default_rng(4),cfg)
            self.assertTrue(np.isfinite(result.centers).all())
            self.assertTrue(np.isfinite(result.diagnostics["best_fitness"]))

    def test_dunn_known_no_ties_answer(self):
        rows=[]
        for method,offset in [("FCM",0),("PFCM",5)]:
            for i in range(5):
                rows.append({"dataset":"fixture","method":method,
                             "accuracy_purity":offset+i,"ari":offset+i,"nmi":offset+i})
        _,pairs=tests(rows,["FCM","PFCM"],["fixture"],.05)
        # Pooled ranks 1..10, mean ranks 3 vs 8; variance=110/12.
        z=5/np.sqrt((110/12)*(.2+.2))
        for pair in pairs:
            self.assertAlmostEqual(pair["z"],z)
            self.assertAlmostEqual(pair["p_bonferroni"],2*norm.sf(z))
            self.assertEqual(pair["family_size"],1)

    def test_external_methods_never_silently_substituted(self):
        X,_,_=load_dataset("iris")
        for name in ("GA-IFWCOM","SCA-FPCOM"):
            with self.assertRaises(NotImplementedError):
                fit_method(name,X,3,np.random.default_rng(1),self.cfg)

    def test_invalid_fuzzifier_bounds_rejected(self):
        cfg=copy.deepcopy(self.cfg)
        cfg["parameter_bounds"]["w"]=[1.,5.]
        with self.assertRaises(ValueError):
            validate_config(cfg)

if __name__=="__main__":
    unittest.main(verbosity=2)
