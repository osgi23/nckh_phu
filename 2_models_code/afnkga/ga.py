"""AF-NKGA search: partition crossover, NK mutations and local search.

Operator names follow the released NKGAclust source (px, mutationReclassify,
mutationMerge, mutationSplit, LsFi), but every body here is written against the
fitness in model.py. Nothing in this file was copied from that source.
"""
import numpy as np

from afnkga.model import canonical


def local_search(fitness, z, rng, sweeps=1):
    """First-improvement over labels available in each point's neighbourhood.

    Uses Fitness.delta, so one move costs O(K) instead of a full evaluation.
    """
    z = np.asarray(z, dtype=int).copy()
    n = len(z)
    for _ in range(sweeps):
        improved = False
        for i in rng.permutation(n):
            i = int(i)
            options = fitness.g.neighbour_labels(z, i) | {0}
            options.discard(int(z[i]))
            best, gain = None, -1e-12
            for label in options:
                d = fitness.delta(z, i, label)
                if d < gain:
                    best, gain = label, d
            if best is not None:
                z[i] = best
                improved = True
        if not improved:
            break
    return z


def partition_crossover(fitness, blue, red):
    """Return the best offspring reachable by choosing, per component, which
    parent's labels to take.

    The vertices where the parents differ are split into connected components
    of the dependency graph. No edge joins two differing vertices of different
    components (such an edge would have merged them), so each component's
    contribution is independent and can be optimised separately. The result is
    therefore the best of 2^q recombinations, computed in O(|E| + n).
    """
    g = fitness.g
    blue = np.asarray(blue, dtype=int)
    red = np.asarray(red, dtype=int)
    differ = blue != red
    if not differ.any():
        return blue.copy(), 0

    n = len(blue)
    adjacency = [[] for _ in range(n)]
    for i, j in zip(g.edge_i, g.edge_j):
        if differ[i] and differ[j]:
            adjacency[i].append(j)
            adjacency[j].append(i)

    component = -np.ones(n, dtype=int)
    count = 0
    for start in range(n):
        if not differ[start] or component[start] >= 0:
            continue
        stack = [start]
        component[start] = count
        while stack:
            u = stack.pop()
            for v in adjacency[u]:
                if component[v] < 0:
                    component[v] = count
                    stack.append(v)
        count += 1

    child = blue.copy()
    for c in range(count):
        mask = component == c
        trial = child.copy()
        trial[mask] = red[mask]
        if fitness(trial) < fitness(child):
            child = trial
    return child, count


def mutate_reclassify(fitness, z, rng):
    z = z.copy()
    i = int(rng.integers(len(z)))
    options = list((fitness.g.neighbour_labels(z, i) | {0}) - {int(z[i])})
    if options:
        z[i] = int(rng.choice(options))
    return z


def mutate_merge(z, rng):
    z = z.copy()
    labels = np.unique(z[z > 0])
    if len(labels) < 2:
        return z
    a, b = rng.choice(labels, size=2, replace=False)
    z[z == b] = a
    return z


def mutate_split(fitness, z, rng):
    """Split one cluster by growing a region from a random seed inside it."""
    z = z.copy()
    labels = np.unique(z[z > 0])
    if not len(labels):
        return z
    target = int(rng.choice(labels))
    members = np.flatnonzero(z == target)
    if len(members) < 4:
        return z
    g = fitness.g
    seed = int(rng.choice(members))
    inside = set(members.tolist())
    taken = {seed}
    frontier = [seed]
    limit = max(len(members)//2, 1)
    while frontier and len(taken) < limit:
        u = frontier.pop()
        for j in g.group[u]:
            j = int(j)
            if j in inside and j not in taken:
                taken.add(j)
                frontier.append(j)
    if 0 < len(taken) < len(members):
        z[list(taken)] = int(z[z > 0].max())+1
    return z


def tournament(fitness_values, rng, size=2):
    picks = rng.integers(0, len(fitness_values), size=size)
    return int(picks[np.argmin(fitness_values[picks])])


def run(fitness, rng, seeds=(), population=30, generations=40,
        crossover_rate=0.9, ls_sweeps=1, elite=1, init_local_search=True):
    """Minimise `fitness` over label vectors. Returns (best_z, best_f, trace).

    init_local_search=False leaves the starting population untouched by local
    search. Local search consults the fitness, so with it enabled two variants
    that differ only in lambda do NOT start from the same population. Disable it
    for the controlled lambda-on/lambda-off pair the research note asks for.
    """
    g = fitness.g
    n = g.n
    polish = (lambda z: local_search(fitness, z, rng, ls_sweeps)) if init_local_search else (lambda z: z)
    pop = []
    for z in seeds:
        pop.append(polish(canonical(z, g)))
        if len(pop) >= population:
            break
    while len(pop) < population:
        k = int(rng.integers(2, max(3, min(12, n//5))))
        z = rng.integers(1, k+1, size=n)
        pop.append(polish(canonical(z, g)))
    pop = [canonical(z, g) for z in pop]
    values = np.array([fitness(z) for z in pop])

    order = int(values.argmin())
    best, best_f = pop[order].copy(), float(values[order])
    trace = [{"generation": 0, "best_fitness": best_f,
              "clusters": int(len(np.unique(best[best > 0]))),
              "noise": int((best == 0).sum()), "evaluations": fitness.evaluations}]

    for generation in range(1, generations+1):
        children = []
        px_components = 0
        while len(children) < population:
            pa = pop[tournament(values, rng)]
            pb = pop[tournament(values, rng)]
            if rng.random() < crossover_rate:
                child, comps = partition_crossover(fitness, pa, pb)
                px_components += comps
            else:
                child = pa.copy()
            roll = rng.random()
            if roll < 0.5:
                child = mutate_reclassify(fitness, child, rng)
            elif roll < 0.75:
                child = mutate_merge(child, rng)
            else:
                child = mutate_split(fitness, child, rng)
            children.append(canonical(local_search(fitness, child, rng, ls_sweeps), g))

        child_values = np.array([fitness(z) for z in children])
        if elite:
            keep = np.argsort(values, kind="stable")[:elite]
            worst = np.argsort(-child_values, kind="stable")[:elite]
            for slot, source in zip(worst, keep):
                children[slot] = pop[source].copy()
                child_values[slot] = values[source]
        pop, values = children, child_values

        order = int(values.argmin())
        if values[order] < best_f:
            best, best_f = pop[order].copy(), float(values[order])
        trace.append({"generation": generation, "best_fitness": best_f,
                      "clusters": int(len(np.unique(best[best > 0]))),
                      "noise": int((best == 0).sum()),
                      "px_components": px_components,
                      "evaluations": fitness.evaluations})
    return best, best_f, trace
