"""BLUE | FCM: Eq.(5)-(7), random normalized partition initialization."""
from common.numerics import random_partition_centers, solve_fcm

def fit(X, k, rng, cfg):
    centers = random_partition_centers(X, k, rng, cfg["w"])
    return solve_fcm(X, centers, cfg["w"], cfg["max_iter"], cfg["tol"], cfg.get("stop_criterion", "objective"), cfg.get("stop_mode", "absolute"))
