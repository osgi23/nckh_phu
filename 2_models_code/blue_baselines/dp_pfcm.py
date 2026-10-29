"""BLUE | Density Peak + PFCM; A1 in Table 11-13."""
from common.density_peak import density_peak_centers
from common.numerics import solve_pfcm

def fit(X, k, rng, cfg):
    centers, diagnostics = density_peak_centers(X, k, cfg)
    result = solve_pfcm(X, centers, cfg)
    result.diagnostics["dpc"] = diagnostics
    return result
