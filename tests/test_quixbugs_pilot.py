import unittest
from lab.quixbugs_pilot import (
    PILOT, HOLDOUT, BUDGETS, METHODS, domain_probes, generate, random_probe
)
from lab.quixbugs_screen import PROGRAMS
from random import Random

class PilotTests(unittest.TestCase):
    def test_split_is_disjoint_and_complete(self):
        self.assertEqual(set(PILOT) | set(HOLDOUT), set(PROGRAMS))
        self.assertEqual(set(PILOT) & set(HOLDOUT), set())
        self.assertEqual(len(HOLDOUT), 16)

    def test_budget_exact(self):
        for name in PILOT:
            for method in METHODS:
                for budget in BUDGETS:
                    xs = generate(name, method, budget, 123)
                    self.assertEqual(len(xs), budget)

    def test_reproducible(self):
        for name in PILOT:
            for method in METHODS:
                self.assertEqual(generate(name, method, 12, 50),
                                 generate(name, method, 12, 50))

    def test_hybrid_three_edges(self):
        for name in PILOT:
            probes = generate(name, "hybrid", 12, 1)
            self.assertEqual(probes[:3], list(domain_probes(name)[:3]))

    def test_shared_random_tail(self):
        for name in PILOT:
            # Shared RNG seed, hence the first nine random probes in hybrid
            # equal the first nine random probes in the fully random strategy.
            a = generate(name, "random", 12, 1)
            b = generate(name, "hybrid", 12, 1)
            self.assertEqual(a[:9], b[3:])

    def test_targeted_has_no_random(self):
        for name in PILOT:
            self.assertEqual(generate(name, "targeted", 12, 1), list(domain_probes(name)))

    def test_invalid_method_rejected(self):
        with self.assertRaises(ValueError):
            generate(PILOT[0], "oracle", 12, 1)
        with self.assertRaises(ValueError):
            generate(PILOT[0], "random", 20, 1)
        with self.assertRaises(ValueError):
            domain_probes("flatten")

    def test_random_domains_simple(self):
        rng = Random(17)
        for _ in range(100):
            (n,) = random_probe("bitcount", rng)
            self.assertGreaterEqual(n, 0)
            a, b = random_probe("gcd", rng)
            self.assertGreaterEqual(min(a,b), 0)
            arr, k = random_probe("bucketsort", rng)
            self.assertTrue(k >= 1 and all(0<=n<k for n in arr))
            arr, x = random_probe("find_first_in_sorted", rng)
            self.assertEqual(arr, sorted(arr))

if __name__ == "__main__":
    unittest.main()
