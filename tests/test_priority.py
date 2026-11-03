import unittest
from unittest.mock import patch

from lab.priority import features, distance, prioritize, prioritization_cost
from lab.quixbugs_pilot import PILOT, domain_probes
from lab.quixbugs_diversity import analyze

class InputDiversityTests(unittest.TestCase):
    def test_jaccard(self):
        a = features((0,))
        self.assertEqual(distance(a,a), 0)
        self.assertGreater(distance(a,features((10,))), 0)
        self.assertGreaterEqual(distance(a,features((10,))), 0)
        self.assertLessEqual(distance(a,features((10,))), 1)

    def test_budget_and_permutation(self):
        for name in PILOT:
            cases = domain_probes(name)
            indexes = prioritize(cases)
            self.assertEqual(sorted(indexes), list(range(12)))
            self.assertEqual(len(indexes), 12)

    def test_order_unchanged_under_reordering_of_unique_inputs(self):
        for name in PILOT:
            original = list(domain_probes(name))
            reversed_cases = list(reversed(original))
            old_order = [original[i] for i in prioritize(original)]
            new_order = [reversed_cases[i] for i in prioritize(reversed_cases)]
            self.assertEqual(old_order, new_order)

    def test_no_mutations_and_repeatable(self):
        for name in PILOT:
            cases = domain_probes(name)
            snap = repr(cases)
            self.assertEqual(prioritize(cases), prioritize(cases))
            self.assertEqual(repr(cases), snap)

    def test_missing_and_huge_input_rejected(self):
        with self.assertRaises(ValueError):
            prioritize([])
        with self.assertRaises(ValueError):
            prioritize([(0,)]*513)

    def test_unsupported_data_rejected(self):
        with self.assertRaises(TypeError):
            features((object(),))

    def test_cost(self):
        self.assertEqual(prioritization_cost(12),144)
        with self.assertRaises(ValueError):
            prioritization_cost(-1)

    def test_synthetic_outcomes_without_real_bugs(self):
        # All outcomes constructed as fake fixtures, no repository fault read.
        rows = []
        for name in PILOT:
            flags = [False]*11 + [True]
            rows.append({
                "program": name, "oracle_invalid": 0,
                "priority_indices": list(range(12)),
                "distance_evaluations_upper_bound": 144,
                "outcomes": [{"index": i, "oracle_valid": True,
                              "detected": v} for i,v in enumerate(flags)]})
        result = analyze(rows)
        self.assertEqual(result["summary"][0]["fixed_detected_programs"],0)
        self.assertEqual(result["summary"][-1]["diversity_detected_programs"],4)
        self.assertAlmostEqual(result["summary"][0]["expected_uniform_random_programs"], 4/12)

    def test_priority_is_pure_input_only(self):
        # This operation must work if both oracle and buggy loading are disabled.
        with patch("lab.quixbugs_screen.load_function", side_effect=RuntimeError):
            self.assertEqual(len(prioritize(domain_probes(PILOT[0]))), 12)

if __name__ == "__main__":
    unittest.main()
