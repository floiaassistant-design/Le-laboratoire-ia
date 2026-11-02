import unittest
from random import Random
from lab.quixbugs_external import (
    PROGRAMS, PILOT, REPEATS, BUDGETS, METHODS, edge_probes, random_probe, generate
)

class ExternalPolicyTests(unittest.TestCase):
    def test_disjoint(self):
        self.assertEqual(len(PROGRAMS), 16)
        self.assertFalse(set(PROGRAMS) & set(PILOT))
    def test_all_edges(self):
        for p in PROGRAMS:
            self.assertEqual(len(edge_probes(p)), 12)
    def test_budgets_and_reproducibility(self):
        for p in PROGRAMS:
            for b in BUDGETS:
                for method in METHODS:
                    a = generate(p, method, b, 138)
                    self.assertEqual(len(a), b)
                    self.assertEqual(a, generate(p, method, b, 138))
    def test_hybrid_three_edges(self):
        for p in PROGRAMS:
            self.assertEqual(generate(p,"hybrid",12,7)[:3],list(edge_probes(p)[:3]))
    def test_random_tail_common(self):
        for p in PROGRAMS:
            self.assertEqual(generate(p,"hybrid",12,7)[3:], generate(p,"random",12,7)[:9])
    def test_domain_semantics(self):
        r=Random(100)
        for _ in range(50):
            arr, k = random_probe("kth",r)
            self.assertTrue(0 <= k < len(arr))
            digits, = random_probe("next_palindrome",r)
            self.assertEqual(digits, digits[::-1])
            start, end = random_probe("hanoi",r)[1:]
            self.assertNotEqual(start,end)
            arr, = random_probe("next_permutation",r)
            self.assertEqual(len(arr),len(set(arr)))
    def test_invalid_name(self):
        with self.assertRaises(ValueError):
            generate(PILOT[0], "hybrid",12,1)
    def test_repeats(self):
        self.assertGreaterEqual(REPEATS, 5)

if __name__ == "__main__": unittest.main()
