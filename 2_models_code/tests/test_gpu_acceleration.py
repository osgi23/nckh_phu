import unittest
import numpy as np
from common.meta_pfcm import PFCMSearch
from common.gpu_evaluator import is_gpu_supported, GPUBatchedPFCM

class TestGPUAcceleration(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        self.N, self.D, self.K = 150, 4, 3
        self.X = np.random.rand(self.N, self.D)
        self.cfg = {
            "population": 20,
            "generations": 5,
            "seed_jitter": 0.05,
            "parameter_bounds": {
                "a": [0.1, 5.0], "b": [0.1, 5.0],
                "w": [1.1, 5.0], "eta": [1.1, 5.0]
            },
            "a": 1.0, "b": 1.0, "w": 2.0, "eta": 2.0,
            "gamma_scale": 1.0,
            "gamma_refresh": "each_step",
            "fitness": "fcm_reference",
            "fitness_reference_w": 2.0,
            "lamarckian": False,
            "gpu_double_precision": True,
            "device": "auto",
            "use_gpu": True
        }

    def test_cpu_fallback_consistency(self):
        # Even without GPU, PFCMSearch works reliably on CPU
        cfg_cpu = dict(self.cfg, use_gpu=False, device="cpu")
        search_cpu = PFCMSearch(self.X, self.K, cfg_cpu)
        anchors = self.X[:self.K].copy()
        rng = np.random.default_rng(42)
        initial = search_cpu.initial(anchors, rng)
        updated, scores = search_cpu.evaluate(initial)
        self.assertEqual(len(scores), self.cfg["population"])
        self.assertTrue(np.all(np.isfinite(scores)))

    @unittest.skipUnless(is_gpu_supported(), "CUDA is not available in environment")
    def test_gpu_numerical_equivalence(self):
        cfg_cpu = dict(self.cfg, use_gpu=False, device="cpu")
        cfg_gpu = dict(self.cfg, use_gpu=True, device="cuda")
        
        search_cpu = PFCMSearch(self.X, self.K, cfg_cpu)
        search_gpu = PFCMSearch(self.X, self.K, cfg_gpu)
        
        anchors = self.X[:self.K].copy()
        rng = np.random.default_rng(123)
        initial = search_cpu.initial(anchors, rng)
        
        up_cpu, sc_cpu = search_cpu.evaluate(initial)
        up_gpu, sc_gpu = search_gpu.evaluate(initial)
        
        # Verify close numerical match between CPU and GPU
        np.testing.assert_allclose(sc_gpu, sc_cpu, rtol=1e-3, atol=1e-3)

if __name__ == "__main__":
    unittest.main()
