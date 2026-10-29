"""ORANGE | DP-PSO-PFCM (A3): inertia increases 0.4 -> 0.9, c1=c2=2."""
import numpy as np
from common.meta_pfcm import fit_meta

def particle_swarm(problem, initial, rng, cfg):
    pop, fitness = problem.evaluate(initial)
    personal, personal_cost = pop.copy(), fitness.copy()
    i = int(fitness.argmin())
    best, best_cost = pop[i].copy(), float(fitness[i])
    limit = cfg["pso_velocity_fraction"]*(problem.high-problem.low)
    velocity = rng.uniform(-limit, limit, pop.shape)
    trace = [{"generation": 0, "best_fitness": best_cost, "evaluations": problem.evaluations}]
    for generation in range(1, cfg["generations"]+1):
        fraction = (generation-1)/max(cfg["generations"]-1, 1)
        inertia = cfg["pso_inertia_start"]+fraction*(cfg["pso_inertia_end"]-cfg["pso_inertia_start"])
        velocity = (inertia*velocity +
                    cfg["pso_c1"]*rng.random(pop.shape)*(personal-pop) +
                    cfg["pso_c2"]*rng.random(pop.shape)*(best-pop))
        velocity = np.clip(velocity, -limit, limit)
        pop, fitness = problem.evaluate(pop+velocity)
        better = fitness < personal_cost
        personal[better], personal_cost[better] = pop[better], fitness[better]
        i = int(fitness.argmin())
        if fitness[i] < best_cost:
            best, best_cost = pop[i].copy(), float(fitness[i])
        trace.append({"generation": generation, "best_fitness": best_cost,
                      "inertia": inertia, "evaluations": problem.evaluations})
    return best, best_cost, trace

def fit(X, k, rng, cfg):
    return fit_meta(X, k, rng, cfg, particle_swarm)
