"""EXP-015 deterministic design-audit checks; not an evaluation of LLM skill."""
from __future__ import annotations

import copy
import json
import unittest

from lab.exp010a_adaptive import choose
from lab.exp011_manual import task_profile
from lab.exp014_neutral_padding import MANIFEST, NUMBER, variants
from lab.exp015_content_router import (
    NEGATIVE_CONTROL, STAGE, audit, candidate_route, content_profile, summary,
)


def fixture():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


class TestEXP015ContentRouter(unittest.TestCase):
    def test_frozen_baseline_still_uses_length_thresholds(self):
        for case in fixture()["cases"]:
            items = variants(case["question"])
            self.assertEqual(
                [choose(task_profile(q, case["id"] + "-" + k), "adaptive")
                 for k, q in items.items()],
                ["single", "parallel", "review"],
            )

    def test_candidate_uses_numeric_literals_not_word_count(self):
        self.assertEqual(candidate_route("What is 12 plus 5?", "short"), "single")
        self.assertEqual(candidate_route("Add 12, 5, and 3.", "multi"), "parallel")
        self.assertEqual(candidate_route("Add 12 and 5, then subtract 3.", "staged"), "review")
        self.assertEqual(candidate_route("Add 12 and 5. LATER compute.", "case"), "review")

    def test_same_route_for_all_registered_padding_variants(self):
        for case in fixture()["cases"]:
            routes = [candidate_route(q, case["id"] + "-" + name)
                      for name, q in variants(case["question"]).items()]
            self.assertEqual(len(set(routes)), 1)

    def test_development_cases_do_not_imply_measured_difficulty(self):
        result = audit(fixture())
        for i, family in enumerate(result["families"]):
            expected = "single" if i < 3 else "review"
            self.assertTrue(all(v["candidate_route"] == expected
                                for v in family["variants"]))
            self.assertIn("declared_steps_not_measured_difficulty", family)
        self.assertTrue(result["content_features_selected_after_seeing_cases"])

    def test_exact_baseline_and_candidate_flip_counts(self):
        result = audit(fixture())
        self.assertEqual(result["base_families"], 6)
        self.assertEqual(result["total_input_variants"], 18)
        self.assertEqual(result["baseline_short_to_long_flips"], 6)
        self.assertEqual(result["candidate_short_to_long_flips"], 0)

    def test_negative_control_exposes_candidate_fragility(self):
        result = audit(fixture())
        self.assertEqual(result["candidate_negative_control_flips"], 3)
        self.assertEqual([f["negative_control_route_changed"]
                          for f in result["families"]],
                         [True, True, True, False, False, False])
        self.assertEqual(NUMBER.findall(NEGATIVE_CONTROL), [])
        self.assertIsNotNone(STAGE.search(NEGATIVE_CONTROL))

    def test_planned_calls_constant_not_real_model_cost(self):
        result = audit(fixture())
        self.assertEqual(result["baseline_planned_calls"],
                         {"short": 6, "medium": 12, "long": 12})
        self.assertEqual(result["candidate_planned_calls"],
                         {"short": 9, "medium": 9, "long": 9})
        self.assertEqual(result["models_called"], 0)
        self.assertFalse(result["real_model_accuracy_or_cost_measured"])

    def test_candidate_output_reports_no_generalization_claims(self):
        result = audit(fixture())
        self.assertFalse(result["independent_out_of_sample_evaluation"])
        self.assertFalse(result["general_paraphrase_robustness_proven"])
        self.assertNotIn("answer_key", json.dumps(result))
        self.assertNotIn("real_accuracy", json.dumps(summary(result)))

    def test_budget_is_enforced_by_existing_chooser(self):
        self.assertEqual(candidate_route("Add 1 and 2.", "one", budget=0), "blocked")
        self.assertEqual(candidate_route("Add 1 and 2, then 3.", "two", budget=1), "single")
        self.assertEqual(candidate_route("Add 1 and 2, then 3.", "three", budget=2), "review")

    def test_invalid_inputs_rejected(self):
        for question in ("", "No quantities specified.", 123, None, "9" * 6001):
            with self.subTest(question=str(question)[:20]):
                with self.assertRaises(ValueError):
                    content_profile(question, "valid")
        with self.assertRaises(ValueError):
            content_profile("Add 1 and 2", "invalid id", budget=2)

    def test_structural_profile_is_compatible_with_orchestrator(self):
        t = content_profile("Add 1 and 2 and 3.", "three")
        self.assertEqual(t.uncertainty, 0)
        self.assertTrue(t.parallelizable)
        self.assertEqual(t.budget, 2)
        self.assertFalse(t.mandatory_review)

    def test_audit_rejects_unregistered_manifest(self):
        bad = fixture()
        bad["cases"][0]["question"] = "Can you solve 2 + 2?"
        # EXP-014 shape validation does not bind source questions byte for byte;
        # source fingerprint is therefore necessary to trace altered case text.
        self.assertNotEqual(audit(fixture())["source_manifest_sha256"],
                            audit(bad)["source_manifest_sha256"])

    def test_summary_is_exactly_versioned_output(self):
        from pathlib import Path
        path = Path(__file__).resolve().parent.parent / "results" / "exp015-routing-summary.json"
        expected = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(expected, summary(audit(fixture())))

    def test_full_report_deterministic(self):
        self.assertEqual(audit(fixture()), audit(copy.deepcopy(fixture())))


if __name__ == "__main__":
    unittest.main()
