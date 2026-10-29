"""BLUE | Density Peak + FCM; deterministic top rho*delta centers."""
from common.density_peak import density_peak_centers
from common.numerics import solve_fcm

def fit(X, k, rng, cfg):
    centers, diagnostics = density_peak_centers(X, k, cfg)
    result = solve_fcm(X, centers, cfg["w"], cfg["max_iter"], cfg["tol"], cfg.get("stop_criterion", "objective"), cfg.get("stop_mode", "absolute"))
    result.diagnostics["dpc"] = diagnostics
    return result
