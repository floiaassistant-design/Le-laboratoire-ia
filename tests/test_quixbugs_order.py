import unittest

from lab.quixbugs_order import (
    TOTAL_PROBES, PERMUTATIONS, analyze, permutation_orders,
    prefix_hits, probability_hit, PROGRAMS, BUDGETS,
)

class OrderTests(unittest.TestCase):
    def test_combinatorial_probability_simple(self):
        self.assertEqual(probability_hit(0, 12), 0.0)
        self.assertEqual(probability_hit(1, 1), 1 / 12)
        self.assertEqual(probability_hit(12, 1), 1.0)
        self.assertEqual(probability_hit(1, 12), 1.0)
        self.assertEqual(probability_hit(6, 1), .5)
        self.assertEqual(probability_hit(1, 0), 0.0)

    def test_invalid_count(self):
        for n, b in ((-1, 3), (13, 3), (1, -1), (1, 13)):
            with self.assertRaises(ValueError):
                probability_hit(n, b)

    def test_prefix_strict(self):
        actual = [False] * 11 + [True]
        natural = list(range(12))
        self.assertFalse(prefix_hits(actual, natural, 11))
        self.assertTrue(prefix_hits(actual, natural, 12))
        order = [11] + list(range(11))
        self.assertTrue(prefix_hits(actual, order, 1))
        with self.assertRaises(ValueError):
            prefix_hits(actual, [0] * 12, 1)

    def test_reproducibility_and_permutation(self):
        a = permutation_orders(1, 25)
        self.assertEqual(a, permutation_orders(1, 25))
        self.assertEqual(len(a), 25)
        for order in a:
            self.assertEqual(sorted(order), list(range(TOTAL_PROBES)))
        self.assertNotEqual(a, permutation_orders(2, 25))

    def test_all_methods_keep_same_original_cases(self):
        # The new experiment only permutes indexes; nothing is generated.
        from lab.quixbugs_external import edge_probes
        for p in PROGRAMS:
            self.assertEqual(len(edge_probes(p)), TOTAL_PROBES)

    def test_analytic_and_sampled_means_close(self):
        # Independent synthetic indicator arrays validate the statistical
        # calculation; they are NOT benchmark results.
        mocked = []
        for i, p in enumerate(PROGRAMS):
            checks = [{"index": j, "oracle_valid": True,
                       "bug_detected": (j < (i % 5)),
                       "bug_status": "ok"} for j in range(12)]
            mocked.append({"program": p, "oracle_invalid": 0,
                           "input_checks": checks})
        result = analyze(mocked, repeats=600)
        self.assertEqual(result["summary"][-1]["budget"], 12)
        for row in result["summary"]:
            self.assertLess(abs(row["sampled_mean_detected_programs"] -
                                row["expected_random_order_detected_programs"]), 1.0)

    def test_budget_nested(self):
        order = permutation_orders(0, 1)[0]
        outcomes = [(i % 3) == 0 for i in range(12)]
        prev = False
        for b in BUDGETS:
            current = prefix_hits(outcomes, order, b)
            self.assertFalse(prev and not current)
            prev = current

if __name__ == "__main__":
    unittest.main()
