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


def fuzzy_evidence(graph, bank, weights=None):
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

    ei, ej = graph.edge_i, graph.edge_j
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
    return a, b


class Fitness:
    """F(z) = (1-lambda) * F_NK(z) + lambda * F_fuzzy(z), minimised.

    lambda = 0 with a non-adaptive graph is the reference NKCV2 criterion.
    Every factor depends only on (z_i, z_j) and on frozen constants, which is
    what makes delta evaluation and partition crossover exact.
    """

    def __init__(self, graph, evidence=None, lam=0.0):
        if not 0.0 <= lam < 1.0:
            raise ValueError("lam must satisfy 0 <= lam < 1.")
        if lam > 0.0 and evidence is None:
            raise ValueError("lam > 0 needs fuzzy evidence.")
        self.g, self.lam = graph, float(lam)
        self.a, self.b = (None, None) if evidence is None else evidence
        if self.a is not None and len(self.a) != graph.edge_count:
            raise ValueError("Evidence length must match the edge count.")
        self.evaluations = 0

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
        fz = np.array([self._fuzzy_edge(z[g.edge_i[e]], z[g.edge_j[e]], e)
                       for e in range(g.edge_count)])
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
        scale_fz = self.lam/g.edge_count if self.lam > 0.0 else 0.0
        before = after = 0.0
        for e in g.touch[i]:
            a_i, a_j, d = g.edge_i[e], g.edge_j[e], g.edge_d[e]
            zi, zj = int(z[a_i]), int(z[a_j])
            ni = new_label if a_i == i else zi
            nj = new_label if a_j == i else zj
            before += scale_nk*self._nk_edge(zi, zj, d, g.rho[a_j], g.rho[a_i])
            after += scale_nk*self._nk_edge(ni, nj, d, g.rho[a_j], g.rho[a_i])
            if scale_fz:
                before += scale_fz*self._fuzzy_edge(zi, zj, e)
                after += scale_fz*self._fuzzy_edge(ni, nj, e)
        return after-before


def canonical(z, graph):
    """Relabel so each positive label forms one connected component.

    Preserves every same/different relation on graph edges, so the pairwise
    fitness is unchanged; test_afnkga.py checks that invariance.
    """
    z = np.asarray(z, dtype=int).copy()
    n = len(z)
    adjacency = [[] for _ in range(n)]
    for i, j in zip(graph.edge_i, graph.edge_j):
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
