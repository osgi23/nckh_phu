"""PURPLE | Main DP-GA-PFCM: Sec.3.2, Eqs.(14)-(16), Table 5.
Underspecified choices are exposed in configs and ASSUMPTIONS.md.
"""
import numpy as np
from common.meta_pfcm import fit_meta

def genetic_algorithm(problem, initial, rng, cfg):
    pop, fitness = problem.evaluate(initial)
    size, width = pop.shape
    index = int(fitness.argmin())
    best, best_cost = pop[index].copy(), float(fitness[index])
    trace = [{"generation": 0, "best_fitness": best_cost,
              "evaluations": problem.evaluations}]
    for generation in range(1, cfg["generations"]+1):
        # Positive minimizing loss -> inverse-loss roulette. Choice missing in paper.
        weights = 1.0/np.maximum(fitness, 1e-12)
        probabilities = weights/weights.sum()
        parents = pop[rng.choice(size, size=size, p=probabilities)].copy()
        children = parents.copy()
        for j in range(0, size-1, 2):
            if rng.random() < cfg["crossover_rate"]:
                r = rng.random()  # one coefficient for a pair of chromosomes
                children[j] = r*parents[j]+(1-r)*parents[j+1]
                children[j+1] = r*parents[j+1]+(1-r)*parents[j]
        # Sec.2.3: mutate one randomly selected gene per selected chromosome.
        for i in range(size):
            if rng.random() < cfg["mutation_rate"]:
                j = int(rng.integers(width))
                sign = rng.choice([-1.0, 1.0])
                q = 2.0**(-rng.random()*cfg["mutation_precision"])
                extent = cfg["mutation_range"]*(problem.high[j]-problem.low[j])
                children[i, j] += sign*extent*q
        children, next_fitness = problem.evaluate(children)
        elite = cfg["elite_count"]
        if elite:
            top = np.argsort(fitness, kind="stable")[:elite]
            worst = np.argsort(-next_fitness, kind="stable")[:elite]
            children[worst], next_fitness[worst] = pop[top], fitness[top]
        pop, fitness = children, next_fitness
        index = int(fitness.argmin())
        if fitness[index] < best_cost:
            best, best_cost = pop[index].copy(), float(fitness[index])
        trace.append({"generation": generation, "best_fitness": best_cost,
                      "evaluations": problem.evaluations})
    return best, best_cost, trace

def fit(X, k, rng, cfg):
    return fit_meta(X, k, rng, cfg, genetic_algorithm)
