"""ORANGE | DP-SCA-PFCM (A4): original SCA sine/cosine position updates.
SCA amplitude=2 and linear schedule are assumptions for this integration.
Source: Mirjalili 2016, DOI 10.1016/j.knosys.2015.12.022.
"""
import numpy as np
from common.meta_pfcm import fit_meta

def sine_cosine(problem, initial, rng, cfg):
    pop, fitness = problem.evaluate(initial)
    i = int(fitness.argmin())
    best, best_cost = pop[i].copy(), float(fitness[i])
    trace = [{"generation": 0, "best_fitness": best_cost, "evaluations": problem.evaluations}]
    for generation in range(1, cfg["generations"]+1):
        r1 = cfg["sca_amplitude"]*(1-generation/cfg["generations"])
        angle = rng.uniform(0, 2*np.pi, pop.shape)
        destination = rng.uniform(0, 2, pop.shape)
        wave = np.where(rng.random(pop.shape) < 0.5, np.sin(angle), np.cos(angle))
        pop, fitness = problem.evaluate(pop+r1*wave*np.abs(destination*best-pop))
        i = int(fitness.argmin())
        if fitness[i] < best_cost:
            best, best_cost = pop[i].copy(), float(fitness[i])
        trace.append({"generation": generation, "best_fitness": best_cost,
                      "amplitude": r1, "evaluations": problem.evaluations})
    return best, best_cost, trace

def fit(X, k, rng, cfg):
    return fit_meta(X, k, rng, cfg, sine_cosine)
