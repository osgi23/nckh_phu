"""ORANGE | DP-FBI-PFCM (A5): two teams, A1/A2/B1/B2.
FBI structure: Chou & Nguyen 2020 DOI 10.1016/j.asoc.2020.106339.
Equations checked against 'Overview (FBI and SMA)', Eqs.(1)-(6),
Qiu et al. 2024 DOI 10.1038/s41598-024-59064-w (original FBI only).
This is a documented integration, not the authors' unpublished code.
"""
import numpy as np
from common.meta_pfcm import fit_meta

def forensic_investigation(problem, initial, rng, cfg):
    A, fa = problem.evaluate(initial)
    B, fb = A.copy(), fa.copy()  # two independent teams after initialization
    size, width = A.shape
    i = int(fa.argmin())
    best, best_cost = A[i].copy(), float(fa[i])
    trace = [{"generation": 0, "best_fitness": best_cost, "evaluations": problem.evaluations}]
    def accept(pop, cost, candidates):
        candidates, fc = problem.evaluate(candidates)
        better = fc < cost
        pop[better], cost[better] = candidates[better], fc[better]
        return pop, cost
    def update_best(pop, cost):
        nonlocal best, best_cost
        i = int(cost.argmin())
        if cost[i] < best_cost:
            best, best_cost = pop[i].copy(), float(cost[i])
    for generation in range(1, cfg["generations"]+1):
        # A1: two distinct peers, excluding the current investigator.
        candidates = A.copy()
        for i in range(size):
            peers = np.delete(np.arange(size), i)
            j, h = rng.choice(peers, 2, replace=False)
            candidates[i] = A[i]+rng.uniform(-1, 1, width)*(A[i]-(A[j]+A[h])/2)
        A, fa = accept(A, fa, candidates)
        update_best(A, fa)
        # A2: lower-quality investigators are more likely to relocate.
        spread = float(fa.max()-fa.min())
        if spread > 1e-12:
            probability = (fa.max()-fa)/spread
            active = np.flatnonzero(rng.random(size) > probability)
            candidates = A[active].copy()
            for row, i in enumerate(active):
                peers = np.delete(np.arange(size), i)
                j, h, l = rng.choice(peers, 3, replace=False)
                mask = rng.random(width) < rng.random(width)
                trial = best+A[j]+rng.random(width)*(A[h]-A[l])
                candidates[row, mask] = trial[mask]
            if len(active):
                updated, costs = problem.evaluate(candidates)
                better = costs < fa[active]
                selected = active[better]
                A[selected], fa[selected] = updated[better], costs[better]
        update_best(A, fa)
        # B1: pursuing the best discovered location.
        candidates = rng.random(B.shape)*B+rng.random(B.shape)*(best-B)
        B, fb = accept(B, fb, candidates)
        update_best(B, fb)
        # B2: move depending on whether a randomly selected peer is better.
        candidates = B.copy()
        for i in range(size):
            j = int(rng.choice(np.delete(np.arange(size), i)))
            r1, r2 = rng.random(width), rng.random(width)
            if fb[j] < fb[i]:
                candidates[i] = B[j]+r1*(B[j]-B[i])+r2*(best-B[j])
            else:
                candidates[i] = B[i]+r1*(B[i]-B[j])+r2*(best-B[i])
        B, fb = accept(B, fb, candidates)
        update_best(B, fb)
        trace.append({"generation": generation, "best_fitness": best_cost,
                      "evaluations": problem.evaluations})
    return best, best_cost, trace

def fit(X, k, rng, cfg):
    return fit_meta(X, k, rng, cfg, forensic_investigation)
