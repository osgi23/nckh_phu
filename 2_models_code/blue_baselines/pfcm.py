"""BLUE | PFCM: Eq.(8)-(12); defaults a=b=1, w=eta=2 are assumptions."""
from common.numerics import random_partition_centers, solve_pfcm

def fit(X, k, rng, cfg):
    centers = random_partition_centers(X, k, rng, cfg["w"])
    return solve_pfcm(X, centers, cfg)
