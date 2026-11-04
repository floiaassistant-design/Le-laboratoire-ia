"""EXP-010B offline evaluation controls, including deliberately misleading critics."""
import copy
import json
import unittest

from lab.exp010b_benchmark import (
    MANIFEST, evaluate, evaluate_case, validate_fixture,
)


def fixtures():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


class SyntheticEvaluationTests(unittest.TestCase):
    def test_fixture_contains_16_cases(self):
        source = fixtures()
        validate_fixture(source)
        self.assertEqual(len(source["cases"]), 16)

    def test_four_policies_compare_same_cases(self):
        result = evaluate(fixtures())
        self.assertEqual(result["evaluations"], 64)
        self.assertEqual({s["total_cases"] for s in result["summary"]}, {16})

    def test_no_models_or_real_accuracy_claimed(self):
        result = evaluate(fixtures())
        self.assertEqual(result["models_called"], 0)
        self.assertFalse(result["real_world_accuracy_measured"])
        self.assertFalse(result["causal_superiority_claimed"])

    def test_simple_adaptive_route(self):
        record = evaluate_case(fixtures()["cases"][0], "adaptive")
        self.assertEqual((record["route"], record["calls"]), ("single", 1))

    def test_parallel_adaptive_route(self):
        record = evaluate_case(fixtures()["cases"][4], "adaptive")
        self.assertEqual((record["route"], record["calls"]), ("parallel", 2))

    def test_uncertain_adaptive_route(self):
        record = evaluate_case(fixtures()["cases"][8], "adaptive")
        self.assertEqual((record["route"], record["calls"]), ("review", 2))

    def test_mandatory_review_is_enforced(self):
        record = evaluate_case(fixtures()["cases"][12], "adaptive")
        self.assertEqual(record["route"], "review")

    def test_mandatory_review_underbudget_blocks(self):
        record = evaluate_case(fixtures()["cases"][15], "adaptive")
        self.assertEqual((record["status"], record["calls"]), ("blocked", 0))

    def test_adaptive_budget_fallback_for_noncritical_task(self):
        record = evaluate_case(fixtures()["cases"][14], "adaptive")
        self.assertEqual((record["route"], record["calls"]), ("single", 1))

    def test_consensus_can_still_be_wrong(self):
        record = evaluate_case(fixtures()["cases"][6], "adaptive")
        self.assertTrue(record["wrong_consensus"])
        self.assertTrue(record["incorrect"])

    def test_critic_can_approve_wrong_answer(self):
        record = evaluate_case(fixtures()["cases"][10], "adaptive")
        self.assertTrue(record["false_critic_approval"])

    def test_critic_can_reject_correct_answer(self):
        record = evaluate_case(fixtures()["cases"][11], "adaptive")
        self.assertTrue(record["false_critic_rejection"])
        self.assertTrue(record["abstained"])

    def test_parallel_disagreement_not_counted_as_incorrect_answer(self):
        record = evaluate_case(fixtures()["cases"][5], "adaptive")
        self.assertEqual(record["status"], "unresolved_disagreement")
        self.assertTrue(record["abstained"])
        self.assertFalse(record["incorrect"])

    def test_invalid_ground_truth_symbol_rejected(self):
        source = fixtures()
        source["cases"][0]["expected"] = "SECRET"
        with self.assertRaises(ValueError):
            validate_fixture(source)

    def test_changed_policy_list_rejected(self):
        source = fixtures()
        source["policies"] = ["always_single"]
        with self.assertRaises(ValueError):
            validate_fixture(source)

    def test_missing_case_rejected(self):
        source = fixtures()
        source["cases"].pop()
        with self.assertRaises(ValueError):
            validate_fixture(source)

    def test_invalid_budget_rejected(self):
        source = fixtures()
        source["cases"][2]["budget"] = -1
        with self.assertRaises(ValueError):
            validate_fixture(source)

    def test_each_policy_partition_exhaustive(self):
        result = evaluate(fixtures())
        for s in result["summary"]:
            self.assertEqual(s["correct"] + s["incorrect"] +
                             s["blocked"] + s["abstained"], 16)

    def test_spent_never_exceeds_each_task_budget(self):
        source = fixtures()
        result = evaluate(source)
        budgets = {c["id"]: c["budget"] for c in source["cases"]}
        for item in result["per_case"]:
            self.assertLessEqual(item["calls"], budgets[item["case_id"]])

    def test_repeated_evaluation_is_deterministic_without_mutation(self):
        source = fixtures()
        original = copy.deepcopy(source)
        first = evaluate(source)
        second = evaluate(source)
        self.assertEqual(first, second)
        self.assertEqual(source, original)


if __name__ == "__main__":
    unittest.main()
