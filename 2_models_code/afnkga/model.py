"""AF-NKGA: graph, fuzzy pairwise evidence and the proposed fitness.

Implements the design in
4_documents/research_notes/kien_truc_nghien_cuu_adaptive_fuzzy_nkga.md.

PROVENANCE — read this before citing anything here as a reproduction.
The design is INSPIRED BY the NK hybrid GA for clustering of Tinos, Zhao,
Chicano & Whitley (IEEE TEC; preprint arXiv:2402.03813). Of that work this
session could read the released source (github.com/rtinos/NKGAclust) but NOT
the paper text, because arxiv.org is unreachable here. From the source we took
two concrete facts:

  * solutions are label vectors with label 0 meaning noise;
  * the three distance thresholds come from a three-sigma rule over the edge
    distances, set in nk.h as dt0 = mean, dt1 = mean + 2*sd, dt2 = mean + sd
    (note dt2 < dt1, which does not follow the names).

The per-edge factor below is OUR OWN explicit definition. It is NOT NKCV2 and
must not be presented as NKCV2: the full NKCV2 factor was not read. What we did
read of comp_fi shows each factor is bounded by rho[j], and that bound is kept
here so the normaliser stays a constant of the data.

Local scaling follows Zelnik-Manor & Perona, Self-Tuning Spectral Clustering
(NIPS 2004): sigma_i is the distance to the ks-th nearest neighbour.
"""
import numpy as np
from scipy.spatial.distance import cdist

EPS = 1e-12


class Graph:
    """Adaptive NK neighbourhood graph, frozen for a whole AF-NKGA run."""

    def __init__(self, X, neighbours=3, ks=7, adaptive=True, block=512):
        self.X = np.asarray(X, dtype=float)
        n = len(self.X)
        if not 1 <= neighbours < n:
            raise ValueError("neighbours must satisfy 1 <= K < n.")
        self.n, self.K, self.adaptive = n, int(neighbours), bool(adaptive)
        ks = min(max(int(ks), 1), n-1)

        d2 = cdist(self.X, self.X, metric="sqeuclidean")
        np.fill_diagonal(d2, 0.0)
        euclid = np.sqrt(np.maximum(d2, 0.0))
        self.sigma = np.maximum(np.sqrt(np.partition(d2, ks, axis=1)[:, ks]), EPS)
        if adaptive:
            # Dimensionless distance; a pair is "close" relative to how dense
            # both of its endpoints' own neighbourhoods are.
            scale = np.sqrt(self.sigma[:, None]*self.sigma[None, :])
            self.dist = euclid/scale
        else:
            self.dist = euclid

        # Density on the SAME distances the thresholds use, so that switching
        # to adaptive distances cannot leave density and thresholds on
        # different scales. Choice of ours, not of the NK paper.
        radius = float(np.median(self.dist[self.dist > 0])) if n > 1 else 1.0
        self.rho = (self.dist <= max(radius, EPS)).sum(axis=1).astype(float)-1.0
        self.rho = np.maximum(self.rho, 0.0)
        self.rho_low = float(np.quantile(self.rho, 0.10))

        # Each group holds the K nearest OTHER points under the active metric.
        # Mask the diagonal by assignment: `dist + eye*inf` would make every
        # off-diagonal entry 0*inf = nan, which silently destroys the ordering
        # and lets a point become its own neighbour.
        masked = self.dist.copy()
        np.fill_diagonal(masked, np.inf)
        order = np.argsort(masked, axis=1, kind="stable")
        self.group = order[:, :self.K].astype(int)          # group[i] -> the K js
        self.edge_i = np.repeat(np.arange(n), self.K)
        self.edge_j = self.group.ravel()
        self.edge_d = self.dist[self.edge_i, self.edge_j]

        # Three-sigma rule over edge distances, recomputed on the active metric.
        mean, sd = float(self.edge_d.mean()), float(self.edge_d.std())
        self.c_near, self.c_far = mean, mean+2.0*sd
        if self.c_far <= self.c_near:
            self.c_far = self.c_near+EPS

        # Normaliser: every factor lies in [0, rho_j], so this is the largest
        # value the NK part can take. Computed once from the data, never from
        # the population (per-generation min/max normalisation would make
        # fitness values incomparable across generations).
        self.s_nk = float(self.rho[self.edge_j].sum())+EPS

        # Incidence lists for delta evaluation: changing z_i touches every edge
        # with i at either end, so both directions are needed.
        self.touch = [[] for _ in range(n)]
        for e, (i, j) in enumerate(zip(self.edge_i, self.edge_j)):
            if i == j:
                raise ValueError("Self-loop in the NK graph; neighbour selection is wrong.")
            self.touch[i].append(e)
            self.touch[j].append(e)
        self.touch = [np.asarray(t, dtype=int) for t in self.touch]

    def neighbour_labels(self, z, i):
        """Positive labels present in i's group and in the groups containing i."""
        pool = set()
        for e in self.touch[i]:
            for v in (z[self.edge_i[e]], z[self.edge_j[e]]):
                if v > 0:
                    pool.add(int(v))
        return pool


def fuzzy_evidence(graph, bank, weights=None):
    """Per-edge same-cluster (a) and different-cluster (b) evidence.

    bank: list of (U, T) from reference PFCM models. For model r let l_i be the
    arg-max membership, m_i the top-1 minus top-2 membership margin and
    h_i = m_i * t_{i,l_i}. Then
        a_ij = sum_r pi_r h_i h_j [l_i == l_j]
        b_ij = sum_r pi_r h_i h_j [l_i != l_j]
    Both can be small when the references are unsure. b is NOT 1-a: absence of
    same-cluster evidence is not evidence of being in different clusters.

    Only edges of the graph are filled, so cost is O(|E| * |bank|).
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
        if T is None:
            typ = np.ones(len(U))
        else:
            typ = np.asarray(T, float)[np.arange(len(U)), lab]
        h = np.clip(margin*typ, 0.0, None)
        same = lab[ei] == lab[ej]
        prod = pi*h[ei]*h[ej]
        a += np.where(same, prod, 0.0)
        b += np.where(same, 0.0, prod)
    return a, b


class Fitness:
    """F(z) = (1-lambda) * F_NK(z) + lambda * F_fuzzy(z), to be minimised.

    Every factor depends only on (z_i, z_j) and on quantities frozen at
    construction, so the function decomposes over edges. That is what makes
    delta evaluation and partition crossover exact.
    """

    def __init__(self, graph, evidence=None, lam=0.0):
        if not 0.0 <= lam < 1.0:
            raise ValueError("lam must satisfy 0 <= lam < 1.")
        if lam > 0.0 and evidence is None:
            raise ValueError("lam > 0 needs fuzzy evidence.")
        self.g, self.lam = graph, float(lam)
        self.a, self.b = (None, None) if evidence is None else evidence
        if self.a is not None and len(self.a) != len(graph.edge_i):
            raise ValueError("Evidence length must match the edge count.")
        self.evaluations = 0

    # ---- per-edge factors -------------------------------------------------
    def _nk_edge(self, zi, zj, d, rho_j, rho_i):
        """Our factor, in [0, rho_j]. Graded, so local search gets a gradient."""
        span = self.g.c_far-self.g.c_near
        if zi > 0 and zj > 0:
            if zi == zj:
                # Same cluster is cheap while the pair is close.
                frac = (d-self.g.c_near)/span
            else:
                # Different clusters is cheap while the pair is far apart.
                frac = (self.g.c_far-d)/span
            return rho_j*min(max(frac, 0.0), 1.0)
        if zi == 0:
            # Calling i noise is free only where i is genuinely isolated:
            # low density AND far from this neighbour.
            justified = rho_i <= self.g.rho_low and d > self.g.c_far
            return 0.0 if justified else rho_j
        return 0.0  # a noise neighbour imposes no same/different constraint

    def _fuzzy_edge(self, zi, zj, e):
        if zi > 0 and zj > 0:
            return self.a[e] if zi != zj else self.b[e]
        # Turning an endpoint into noise must not dodge the fuzzy cost, or the
        # search would relabel hard points as noise to get them for free.
        return self.a[e]+self.b[e]

    # ---- aggregate --------------------------------------------------------
    def edge_costs(self, z):
        g = self.g
        z = np.asarray(z, dtype=int)
        nk = np.empty(len(g.edge_i))
        for e, (i, j, d) in enumerate(zip(g.edge_i, g.edge_j, g.edge_d)):
            nk[e] = self._nk_edge(z[i], z[j], d, g.rho[j], g.rho[i])
        if self.lam == 0.0:
            return nk, None
        fz = np.array([self._fuzzy_edge(z[i], z[j], e)
                       for e, (i, j) in enumerate(zip(g.edge_i, g.edge_j))])
        return nk, fz

    def __call__(self, z):
        nk, fz = self.edge_costs(z)
        total = (1.0-self.lam)*nk.sum()/self.g.s_nk
        if self.lam > 0.0:
            total += self.lam*fz.mean()
        self.evaluations += 1
        return float(total)

    def delta(self, z, i, new_label):
        """Exact change in F if z[i] becomes new_label. Touches only i's edges."""
        g, old = self.g, int(z[i])
        if old == new_label:
            return 0.0
        before = after = 0.0
        edges = g.touch[i]
        scale_nk = (1.0-self.lam)/g.s_nk
        scale_fz = self.lam/len(g.edge_i) if self.lam > 0.0 else 0.0
        for e in edges:
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

    Two unconnected fragments that happen to share a label would otherwise make
    the reported cluster count depend on naming. Splitting them preserves every
    same/different relation ON GRAPH EDGES, so the pairwise fitness is
    unchanged - test_afnkga.py checks that invariance.
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
