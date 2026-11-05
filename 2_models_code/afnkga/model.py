"""AF-NKGA: NKCV2 graph and factor, plus the proposed fuzzy-guided term.

PROVENANCE
The NK part of this file is a FAITHFUL port of the released reference source
nk.h from github.com/rtinos/NKGAclust (Tinos, Zhao, Chicano & Whitley, NK
Hybrid Genetic Algorithm for Clustering, IEEE TEC; preprint arXiv:2402.03813).
The paper text was NOT readable in this environment, so every NK detail below
comes from that source, line by line:

  * D[i][j] is the SQUARED Euclidean distance (sqrEucDist), and every threshold
    lives on that scale.
  * dc is the 2nd percentile of the sorted pairwise squared distances
    (percent=2; position=(N(N-1)/2 * 2)/100), as in Rodriguez & Laio (2014).
  * rho[i] = sum_j exp(-(D[i][j]/dc)^2), then divided by its maximum so it
    lands in [0,1]; d_rho = mean(rho) - std(rho), or mean/2 if that is <= 0.
  * The epistasis graph is NOT a k-NN graph. Step 1 gives each vertex one
    in-edge from the nearest object of HIGHER density (the density-peak parent;
    the densest object instead takes its overall nearest neighbour). Step 2
    then adds nearest objects until every vertex has in-degree exactly K.
  * threeSigmaRule over the in-edge distances sets dt0 = mean, dt1 = mean+2sd,
    dt2 = mean+sd. dt2 < dt1, which does not follow the names.
  * In comp_fi the branch order is `x[i]==0`, then `x[i]==x[j]`, then else.
    So a positive-labelled point whose neighbour is NOISE falls through to the
    different-label branch and is charged accordingly - it is not exempt.
  * The total is divided by N*K, the edge count.

The fuzzy evidence (a_ij, b_ij) and the lambda-weighted combination are the
proposed contribution and are NOT part of NKCV2. The adaptive local-scaled
metric (Zelnik-Manor & Perona, NIPS 2004) is likewise an option of ours, off by
default so that `adaptive=False` reproduces the reference criterion.
"""
import numpy as np
from scipy.spatial.distance import cdist

EPS = 1e-12


class Graph:
    """NKCV2 epistasis graph. adaptive=False reproduces the reference source."""

    def __init__(self, X, neighbours=3, ks=7, adaptive=False, dc_percent=2):
        self.X = np.asarray(X, dtype=float)
        n = len(self.X)
        if not 1 <= neighbours < n:
            raise ValueError("neighbours must satisfy 1 <= K < n.")
        self.n, self.K, self.adaptive = n, int(neighbours), bool(adaptive)

        # Squared Euclidean distance, as in the reference source.
        d2 = cdist(self.X, self.X, metric="sqeuclidean")
        np.fill_diagonal(d2, 0.0)
        ks = min(max(int(ks), 1), n-1)
        self.sigma = np.maximum(np.sqrt(np.partition(d2, ks, axis=1)[:, ks]), EPS)
        if adaptive:
            # Proposed option: divide by sigma_i*sigma_j so the squared distance
            # becomes dimensionless. Every threshold below is then recomputed on
            # this scale - a threshold from one metric must never be compared
            # against distances from the other.
            self.dist = d2/(self.sigma[:, None]*self.sigma[None, :])
        else:
            self.dist = d2
        np.fill_diagonal(self.dist, 0.0)

        upper = self.dist[np.triu_indices(n, 1)]
        if not len(upper):
            raise ValueError("Need at least two points.")
        position = min(int(len(upper)*int(dc_percent)/100), len(upper)-1)
        dc = float(np.sort(upper)[position])
        if dc <= EPS:
            positive = upper[upper > EPS]
            dc = float(positive.min()) if len(positive) else 1.0
        self.dc = dc

        # Gaussian kernel density of Rodriguez & Laio, on the squared distance.
        ratio = self.dist/dc
        kernel = np.exp(-ratio*ratio)
        np.fill_diagonal(kernel, 0.0)
        rho = kernel.sum(axis=1)
        peak = rho.max()
        self.rho = rho/peak if peak > 0 else rho
        mean, sd = float(self.rho.mean()), float(self.rho.std())
        self.d_rho = mean-sd if mean-sd > 0.0 else mean/2.0

        self._build_graph()

        mean_d, sd_d = float(self.edge_d.mean()), float(self.edge_d.std())
        self.dt0, self.dt1, self.dt2 = mean_d, mean_d+2.0*sd_d, mean_d+sd_d
        if self.dt1 <= self.dt0:
            self.dt1 = self.dt0+EPS

    def _build_graph(self):
        """Step 1: density-peak parent. Step 2: fill to in-degree K."""
        n, K = self.n, self.K
        big = float(self.dist.max())+1.0
        sources = [[] for _ in range(n)]
        taken = [set() for _ in range(n)]

        higher = self.rho[None, :] > self.rho[:, None]
        masked = np.where(higher, self.dist, np.inf)
        parent = masked.argmin(axis=1)
        no_higher = ~higher.any(axis=1)
        if no_higher.any():
            # Densest object(s): take the overall nearest neighbour instead.
            fallback = self.dist.copy()
            np.fill_diagonal(fallback, big)
            parent[no_higher] = fallback[no_higher].argmin(axis=1)
        for i in range(n):
            sources[i].append(int(parent[i]))
            taken[i].add(int(parent[i]))

        order = np.argsort(np.where(np.eye(n, dtype=bool), big, self.dist),
                           axis=1, kind="stable")
        for i in range(n):
            for j in order[i]:
                if len(sources[i]) >= K:
                    break
                j = int(j)
                if j != i and j not in taken[i]:
                    sources[i].append(j)
                    taken[i].add(j)
            if len(sources[i]) < K:
                raise ValueError("Not enough distinct objects to reach in-degree K.")

        self.group = np.asarray(sources, dtype=int)
        self.edge_i = np.repeat(np.arange(n), K)       # the influenced vertex
        self.edge_j = self.group.ravel()               # the influencing vertex
        if (self.edge_i == self.edge_j).any():
            raise ValueError("Self-loop in the NK graph.")
        self.edge_d = self.dist[self.edge_i, self.edge_j]
        self.edge_count = len(self.edge_i)             # == N*K

        self.touch = [[] for _ in range(n)]
        for e, (i, j) in enumerate(zip(self.edge_i, self.edge_j)):
            self.touch[i].append(e)
            self.touch[j].append(e)
        self.touch = [np.asarray(t, dtype=int) for t in self.touch]

    def neighbour_labels(self, z, i):
        pool = set()
        for e in self.touch[i]:
            for v in (z[self.edge_i[e]], z[self.edge_j[e]]):
                if v > 0:
                    pool.add(int(v))
        return pool


def evidence_edges(graph, bank, per_point=3, pool=30, agree_per_point=0):
    """Choose the pairs the fuzzy evidence is computed on - NOT the NK edges.

    WHY A SEPARATE EDGE SET. Measured: over the NK graph's edges the reference
    models separate only 4-11% of the pairs (wifi 5.9%, pima 9.9%,
    iris 11.6%), because those edges join near neighbours that every model
    keeps together. So b_ij, the different-cluster evidence, had almost no mass
    (mean 0.0001 against a's 0.0149) and the fuzzy term pushed toward merging
    exactly like the NK term. Rebalancing a and b afterwards treats the
    symptom; this addresses the cause by evaluating the evidence where the
    references actually have something to say.

    SELECTION RULE, label-free. For each i, scan its `pool` nearest objects and
    keep the `per_point` nearest ones that at least one reference model assigns
    to a DIFFERENT cluster than i. These are boundary pairs: close enough that
    the partition's choice matters, yet separated by the references, which is
    precisely where b carries information.

    Returns (ei, ej) with i < j, de-duplicated.
    """
    if not bank:
        raise ValueError("The reference bank is empty.")
    labels = [np.asarray(U, float).argmax(axis=1) for U, _ in bank]
    n = graph.n
    pool = min(max(int(pool), 1), n-1)
    order = np.argsort(np.where(np.eye(n, dtype=bool), np.inf, graph.dist),
                       axis=1, kind="stable")[:, :pool]
    # agree_per_point > 0 also keeps the FARTHEST pairs in the pool that every
    # reference agrees belong together. Those carry a_ij, which V_ij charges
    # when the partition separates them, so they are what penalises splitting.
    # Without them the evidence only contains disagreement pairs, which charge
    # b_ij for merging and therefore push one way only - measured: the fuzzy
    # term then raises ARI but the cluster count keeps climbing (19.2 clusters
    # at lambda 0.8 for true k of 2 and 4).
    nk_pairs = {(min(u, v), max(u, v)) for u, v in zip(graph.edge_i, graph.edge_j)}
    pairs = set()
    for i in range(n):
        kept = 0
        for j in order[i]:
            if kept >= int(per_point):
                break
            j = int(j)
            if j == i:
                continue
            if any(lab[i] != lab[j] for lab in labels):
                pairs.add((i, j) if i < j else (j, i))
                kept += 1
        kept_agree = 0
        for j in order[i][::-1]:
            if kept_agree >= int(agree_per_point):
                break
            j = int(j)
            key = (min(i, j), max(i, j))
            if j == i or key in nk_pairs:
                continue    # the NK term already constrains its own neighbours
            if all(lab[i] == lab[j] for lab in labels):
                pairs.add(key)
                kept_agree += 1
    if not pairs:
        # Every reference agrees about every near pair. Nothing to add; the
        # caller must fall back to the NK edges and know that b will be empty.
        return np.empty(0, dtype=int), np.empty(0, dtype=int)
    arr = np.array(sorted(pairs), dtype=int)
    return arr[:, 0], arr[:, 1]


def fuzzy_evidence(graph, bank, weights=None, balance=False, edges=None):
    """See the docstring below; `balance` rebalances b against a.

    MEASURED PROBLEM that `balance` addresses. The evidence lives on the NK
    graph's edges, and those edges join near neighbours, which every reference
    model puts in the same cluster. Over the NK edges the models separate only
    4-11% of the pairs (wifi 5.9%, pima 9.9%, iris 11.6%), so
    mean(b) = 0.0001 against mean(a) = 0.0149. Since V_ij charges b for a
    same-label pair and a for a different-label pair, the fuzzy term is then
    CHEAPER when everything is merged - it pushes the same way as the NK part
    instead of against it, and no value of lambda reverses that.

    balance=True divides each side by its own total mass, so a and b contribute
    equally in aggregate and scarcity no longer decides the direction. This is
    a declared correction for a sampling artefact of the edge set, NOT a
    calibrated probability, and it does not make the evidence more informative
    - it only stops the imbalance from dominating.
    """
    return _fuzzy_evidence(graph, bank, weights=weights, balance=balance, edges=edges)


def _fuzzy_evidence(graph, bank, weights=None, balance=False, edges=None):
    """Per-edge same-cluster (a) and different-cluster (b) evidence.

    For reference model r: l_i = argmax membership, m_i = top1 - top2 margin,
    h_i = m_i * t_{i,l_i}. Then a_ij sums pi_r h_i h_j over models that put i
    and j together, b_ij over models that separate them. b is NOT 1-a: having
    no same-cluster evidence is not evidence of being apart.

    This term is the proposed contribution; it is not part of NKCV2.
    """
    if not bank:
        raise ValueError("The reference bank is empty.")
    m = len(bank)
    weights = np.full(m, 1.0/m) if weights is None else np.asarray(weights, float)
    if len(weights) != m or weights.min() < 0 or weights.sum() <= 0:
        raise ValueError("weights must be non-negative, one per model.")
    weights = weights/weights.sum()

    ei, ej = (graph.edge_i, graph.edge_j) if edges is None else edges
    ei, ej = np.asarray(ei, dtype=int), np.asarray(ej, dtype=int)
    if len(ei) != len(ej):
        raise ValueError("Evidence edge arrays must have equal length.")
    a = np.zeros(len(ei))
    b = np.zeros(len(ei))
    for pi, (U, T) in zip(weights, bank):
        U = np.asarray(U, float)
        if U.shape[1] < 2:
            raise ValueError("A reference model needs at least 2 clusters.")
        lab = U.argmax(axis=1)
        top = np.sort(U, axis=1)
        margin = top[:, -1]-top[:, -2]
        typ = np.ones(len(U)) if T is None else np.asarray(T, float)[np.arange(len(U)), lab]
        h = np.clip(margin*typ, 0.0, None)
        # Rescale per model. MEASURED FAILURE without this: on wifi with a
        # DP-PFCM bank, margin*typicality gave h so small that a <= 4e-9,
        # b <= 3.6e-10 and 100% of edges had a+b < 1e-6. The fuzzy term was
        # then numerically zero, so (1-lam)*F_NK + lam*0 kept exactly the same
        # arg-min as F_NK and lambda had no effect at all (measured delta
        # 0.0000 on both controlled pairs). PFCM typicality is driven by gamma,
        # whose scale is a property of the data, not of the evidence, so the
        # raw product carries no usable scale. Dividing by the model's own
        # maximum keeps the RELATIVE confidence ordering - which is all the
        # evidence is meant to express - and puts h in [0,1].
        peak = float(h.max())
        if peak > 0.0:
            h = h/peak
        same = lab[ei] == lab[ej]
        prod = pi*h[ei]*h[ej]
        a += np.where(same, prod, 0.0)
        b += np.where(same, 0.0, prod)
    if balance:
        a_mass, b_mass = float(a.sum()), float(b.sum())
        if a_mass > 0.0 and b_mass > 0.0:
            scale = 0.5*(a_mass+b_mass)
            a = a*(scale/a_mass)
            b = b*(scale/b_mass)
    return a, b


class Fitness:
    """F(z) = (1-lambda) * F_NK(z) + lambda * F_fuzzy(z), minimised.

    lambda = 0 with a non-adaptive graph is the reference NKCV2 criterion.
    Every factor depends only on (z_i, z_j) and on frozen constants, which is
    what makes delta evaluation and partition crossover exact.
    """

    def __init__(self, graph, evidence=None, lam=0.0, evidence_edges=None):
        """evidence_edges: the (ei, ej) the fuzzy term lives on.

        None means the NK edges, which is what the first prototype did and what
        made b empty. Passing a separate set is the fix. The two sets then
        differ, so the DEPENDENCY graph of the fitness is their UNION, exposed
        below as dep_i/dep_j/dep_touch. Partition crossover and canonical
        relabelling must both use that union: PX decomposes the differing
        vertices into components that it assumes are independent, and a
        component boundary that ignores an evidence edge would make PX return
        something other than the best of 2^q. Likewise canonical splits a label
        into connected components, which would silently flip a pair from "same"
        to "different" across an evidence edge the connectivity test never saw.
        """
        if not 0.0 <= lam < 1.0:
            raise ValueError("lam must satisfy 0 <= lam < 1.")
        if lam > 0.0 and evidence is None:
            raise ValueError("lam > 0 needs fuzzy evidence.")
        self.g, self.lam = graph, float(lam)
        self.a, self.b = (None, None) if evidence is None else evidence

        if evidence_edges is None:
            self.fz_i, self.fz_j = graph.edge_i, graph.edge_j
        else:
            self.fz_i = np.asarray(evidence_edges[0], dtype=int)
            self.fz_j = np.asarray(evidence_edges[1], dtype=int)
            if len(self.fz_i) != len(self.fz_j):
                raise ValueError("Evidence edge arrays must have equal length.")
        self.fz_count = len(self.fz_i)
        if self.a is not None and len(self.a) != self.fz_count:
            raise ValueError("Evidence length must match the evidence edge count.")
        if self.lam > 0.0 and self.fz_count == 0:
            raise ValueError("lam > 0 needs at least one evidence edge.")

        # Union dependency graph.
        if evidence_edges is None or self.lam == 0.0:
            self.dep_i, self.dep_j = graph.edge_i, graph.edge_j
        else:
            stacked = np.concatenate([
                np.stack([graph.edge_i, graph.edge_j], axis=1),
                np.stack([self.fz_i, self.fz_j], axis=1)])
            low = stacked.min(axis=1)
            high = stacked.max(axis=1)
            unique = np.unique(np.stack([low, high], axis=1), axis=0)
            self.dep_i, self.dep_j = unique[:, 0], unique[:, 1]
        self.dep_touch = [[] for _ in range(graph.n)]
        for u, v in zip(self.dep_i, self.dep_j):
            self.dep_touch[u].append(int(v))
            self.dep_touch[v].append(int(u))
        self.dep_touch = [np.asarray(t, dtype=int) for t in self.dep_touch]

        # Which NK edges and which evidence edges each vertex appears in.
        self._nk_touch = graph.touch
        self._fz_touch = [[] for _ in range(graph.n)]
        for e, (u, v) in enumerate(zip(self.fz_i, self.fz_j)):
            self._fz_touch[u].append(e)
            self._fz_touch[v].append(e)
        self._fz_touch = [np.asarray(t, dtype=int) for t in self._fz_touch]
        self.evaluations = 0

    def neighbour_labels(self, z, i):
        """Positive labels on any dependency edge touching i."""
        pool = {int(z[v]) for v in self.dep_touch[i] if z[v] > 0}
        if z[i] > 0:
            pool.add(int(z[i]))
        return pool

    def _nk_edge(self, zi, zj, d, rho_j, rho_i):
        """comp_fi's per-edge contribution. fmax = rho_j, fmin = 0."""
        g = self.g
        fmax = rho_j
        if zi == 0:
            # Noise is free only where the point is sparse AND far from this
            # neighbour. Note the threshold is dt2, not dt1.
            return 0.0 if (rho_i <= g.d_rho and d > g.dt2) else fmax
        if zi == zj:
            if d > g.dt1:
                return fmax
            if d > g.dt0:
                return fmax*(d-g.dt0)/(g.dt1-g.dt0)
            return 0.0
        # Different labels. A noise neighbour (zj == 0) lands here too, exactly
        # as the reference source's branch order dictates.
        if d <= g.dt0:
            return fmax
        if d <= g.dt1:
            return fmax-fmax*(d-g.dt0)/(g.dt1-g.dt0)
        return 0.0

    def _fuzzy_edge(self, zi, zj, e):
        if zi > 0 and zj > 0:
            return self.a[e] if zi != zj else self.b[e]
        # Turning an endpoint into noise must not dodge the fuzzy cost.
        return self.a[e]+self.b[e]

    def edge_costs(self, z):
        g = self.g
        z = np.asarray(z, dtype=int)
        nk = np.empty(g.edge_count)
        for e in range(g.edge_count):
            i, j = g.edge_i[e], g.edge_j[e]
            nk[e] = self._nk_edge(z[i], z[j], g.edge_d[e], g.rho[j], g.rho[i])
        if self.lam == 0.0:
            return nk, None
        fz = np.array([self._fuzzy_edge(z[self.fz_i[e]], z[self.fz_j[e]], e)
                       for e in range(self.fz_count)])
        return nk, fz

    def __call__(self, z):
        nk, fz = self.edge_costs(z)
        total = (1.0-self.lam)*nk.sum()/self.g.edge_count
        if self.lam > 0.0:
            total += self.lam*fz.mean()
        self.evaluations += 1
        return float(total)

    def delta(self, z, i, new_label):
        """Exact change in F if z[i] becomes new_label."""
        g, old = self.g, int(z[i])
        if old == new_label:
            return 0.0
        scale_nk = (1.0-self.lam)/g.edge_count
        before = after = 0.0
        for e in self._nk_touch[i]:
            a_i, a_j, d = g.edge_i[e], g.edge_j[e], g.edge_d[e]
            zi, zj = int(z[a_i]), int(z[a_j])
            ni = new_label if a_i == i else zi
            nj = new_label if a_j == i else zj
            before += scale_nk*self._nk_edge(zi, zj, d, g.rho[a_j], g.rho[a_i])
            after += scale_nk*self._nk_edge(ni, nj, d, g.rho[a_j], g.rho[a_i])
        if self.lam > 0.0:
            scale_fz = self.lam/self.fz_count
            for e in self._fz_touch[i]:
                a_i, a_j = self.fz_i[e], self.fz_j[e]
                zi, zj = int(z[a_i]), int(z[a_j])
                ni = new_label if a_i == i else zi
                nj = new_label if a_j == i else zj
                before += scale_fz*self._fuzzy_edge(zi, zj, e)
                after += scale_fz*self._fuzzy_edge(ni, nj, e)
        return after-before


def dependency_edges(owner):
    """The edge set a pairwise fitness depends on.

    A Fitness exposes the UNION of its NK edges and its evidence edges; a bare
    Graph only has the NK edges. Anything that must preserve the fitness, or
    that decomposes it, has to use this and not the NK edges alone.
    """
    if hasattr(owner, "dep_i"):
        return owner.dep_i, owner.dep_j
    return owner.edge_i, owner.edge_j


def canonical(z, owner):
    """Relabel so each positive label forms one connected component.

    Connectivity is tested on the DEPENDENCY edges. Using only the NK edges
    would split a label across an evidence edge, flipping that pair from "same"
    to "different" and changing the fitness; test_afnkga.py checks the
    invariance that this protects.
    """
    z = np.asarray(z, dtype=int).copy()
    n = len(z)
    dep_i, dep_j = dependency_edges(owner)
    adjacency = [[] for _ in range(n)]
    for i, j in zip(dep_i, dep_j):
        if z[i] > 0 and z[i] == z[j]:
            adjacency[i].append(j)
            adjacency[j].append(i)
    out = np.zeros(n, dtype=int)
    nxt = 0
    for start in range(n):
        if z[start] <= 0 or out[start]:
            continue
        nxt += 1
        stack = [start]
        out[start] = nxt
        while stack:
            u = stack.pop()
            for v in adjacency[u]:
                if not out[v]:
                    out[v] = nxt
                    stack.append(v)
    return out
