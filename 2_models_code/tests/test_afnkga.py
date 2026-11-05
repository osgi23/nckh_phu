"""Property checks for AF-NKGA, one per claim in the research note (section 5).

These verify the implementation against its own stated contract. They do NOT
verify agreement with the NK hybrid GA paper, whose factor definition was not
available to this session.
"""
import itertools
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from afnkga.ga import local_search, partition_crossover
from afnkga.model import (Fitness, Graph, canonical, dependency_edges,
                          evidence_edges, fuzzy_evidence)


def toy(n_per=8, seed=0):
    rng = np.random.default_rng(seed)
    blobs = [rng.normal(c, 0.35, (n_per, 2)) for c in ([0, 0], [4, 0], [2, 4])]
    return np.vstack(blobs)


def toy_bank(X, clusters=3, seed=1):
    """A crude stand-in for a DP-PFCM bank: soft memberships around k-means-ish
    centres. Enough to exercise the evidence maths without pulling in PFCM."""
    rng = np.random.default_rng(seed)
    centres = X[rng.choice(len(X), clusters, replace=False)]
    d2 = ((X[:, None, :]-centres[None, :, :])**2).sum(axis=2)
    U = 1.0/np.maximum(d2, 1e-9)
    U /= U.sum(axis=1, keepdims=True)
    T = U/U.max(axis=1, keepdims=True)
    return [(U, T)]


class AfNkgaProperties(unittest.TestCase):
    def setUp(self):
        self.X = toy()
        self.graph = Graph(self.X, neighbours=3, ks=5, adaptive=False)
        self.bank = toy_bank(self.X)
        # Evidence on a SEPARATE edge set, the configuration the prototype now
        # uses. Falls back to the NK edges when the references agree about
        # every near pair, which the toy data can produce.
        self.fz_edges = evidence_edges(self.graph, self.bank, per_point=2, pool=10)
        if not len(self.fz_edges[0]):
            self.fz_edges = (self.graph.edge_i, self.graph.edge_j)
        self.evidence = fuzzy_evidence(self.graph, self.bank, edges=self.fz_edges)
        self.rng = np.random.default_rng(7)

    def fit(self, lam):
        return Fitness(self.graph, self.evidence, lam=lam,
                       evidence_edges=self.fz_edges)

    def random_z(self, labels=3, noise=0.15):
        z = self.rng.integers(1, labels+1, size=self.graph.n)
        z[self.rng.random(self.graph.n) < noise] = 0
        return z

    # 1. Permuting positive labels must not change the fitness; 0 is excluded.
    def test_label_permutation_invariance(self):
        for lam in (0.0, 0.5):
            f = self.fit(lam)
            z = self.random_z()
            labels = np.unique(z[z > 0])
            mapping = dict(zip(labels, self.rng.permutation(labels)))
            permuted = np.array([mapping.get(v, 0) for v in z])
            self.assertAlmostEqual(f(z), f(permuted), places=12,
                                   msg=f"not label-invariant at lam={lam}")

    # 3. delta() must equal the difference of two full evaluations.
    def test_delta_matches_full_evaluation(self):
        for lam in (0.0, 0.4):
            f = self.fit(lam)
            z = self.random_z()
            for _ in range(40):
                i = int(self.rng.integers(self.graph.n))
                new = int(self.rng.integers(0, 4))
                predicted = f.delta(z, i, new)
                moved = z.copy()
                moved[i] = new
                actual = f(moved)-f(z)
                self.assertAlmostEqual(predicted, actual, places=12,
                                       msg=f"delta wrong at lam={lam}, i={i}")

    # 4. PX must return the best of the 2^q component choices.
    def test_partition_crossover_is_optimal_over_components(self):
        f = self.fit(0.3)
        # Two independent random parents differ almost everywhere, which gives
        # far too many components to enumerate. Perturb a handful of vertices
        # instead, so q stays small and 2^q can be checked exhaustively.
        blue = self.random_z(labels=3)
        red = blue.copy()
        for i in self.rng.choice(self.graph.n, size=5, replace=False):
            red[int(i)] = int(self.rng.integers(0, 4))
        child, components = partition_crossover(f, blue, red)
        if components == 0:
            self.skipTest("parents identical")
        self.assertLessEqual(components, 12, "too many components to enumerate")

        differ = blue != red
        n = len(blue)
        adjacency = [[] for _ in range(n)]
        dep_i, dep_j = dependency_edges(f)
        for i, j in zip(dep_i, dep_j):
            if differ[i] and differ[j]:
                adjacency[i].append(j)
                adjacency[j].append(i)
        comp = -np.ones(n, dtype=int)
        total = 0
        for start in range(n):
            if not differ[start] or comp[start] >= 0:
                continue
            stack = [start]
            comp[start] = total
            while stack:
                u = stack.pop()
                for v in adjacency[u]:
                    if comp[v] < 0:
                        comp[v] = total
                        stack.append(v)
            total += 1
        self.assertEqual(total, components)

        best = min(
            f(np.where(np.isin(comp, [c for c, take in enumerate(choice) if take]),
                       red, blue))
            for choice in itertools.product([False, True], repeat=total))
        self.assertAlmostEqual(f(child), best, places=12,
                               msg="PX did not return the best recombination")

    # 5. Marking an endpoint as noise must not reduce the fuzzy cost of an edge.
    def test_noise_cannot_dodge_fuzzy_cost(self):
        f = self.fit(0.5)
        a, b = self.evidence
        for e in range(len(a)):
            for zi, zj in ((1, 1), (1, 2)):
                paired = f._fuzzy_edge(zi, zj, e)
                self.assertLessEqual(paired, f._fuzzy_edge(0, zj, e)+1e-12)
                self.assertLessEqual(paired, f._fuzzy_edge(zi, 0, e)+1e-12)

    # 6. Canonical relabelling splits disconnected fragments but keeps fitness.
    def test_canonical_preserves_fitness(self):
        f = self.fit(0.35)
        z = self.random_z()
        self.assertAlmostEqual(f(z), f(canonical(z, f)), places=12)

    def test_canonical_makes_labels_connected(self):
        f = self.fit(0.3)
        z = np.ones(self.graph.n, dtype=int)   # one label over three blobs
        out = canonical(z, f)
        dep_i, dep_j = dependency_edges(f)
        adjacency = [[] for _ in range(self.graph.n)]
        for u, v in zip(dep_i, dep_j):
            adjacency[u].append(int(v))
            adjacency[v].append(int(u))
        for label in np.unique(out[out > 0]):
            members = set(np.flatnonzero(out == label).tolist())
            start = next(iter(members))
            seen, stack = {start}, [start]
            while stack:
                u = stack.pop()
                for v in adjacency[u]:
                    if v in members and v not in seen:
                        seen.add(v)
                        stack.append(v)
            self.assertEqual(seen, members, "a canonical label is disconnected")

    # Local search must never make the solution worse.
    def test_local_search_is_monotone(self):
        f = self.fit(0.25)
        z = self.random_z()
        before = f(z)
        after = f(local_search(f, z, np.random.default_rng(3), sweeps=2))
        self.assertLessEqual(after, before+1e-12)

    # lam must stay inside [0, 1) and require evidence when positive.
    def test_configuration_guards(self):
        with self.assertRaises(ValueError):
            self.fit(1.0)
        with self.assertRaises(ValueError):
            Fitness(self.graph, None, lam=0.5)
        with self.assertRaises(ValueError):
            # lam > 0 with an empty evidence edge set must be refused, not
            # silently treated as lam = 0.
            Fitness(self.graph, (np.empty(0), np.empty(0)), lam=0.5,
                    evidence_edges=(np.empty(0, int), np.empty(0, int)))
        with self.assertRaises(ValueError):
            Graph(self.X, neighbours=0)
        with self.assertRaises(ValueError):
            fuzzy_evidence(self.graph, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
