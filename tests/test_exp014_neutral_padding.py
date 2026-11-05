"""Model-free tests of EXP-014 routing sensitivity, never an LLM benchmark."""
import copy
import json
import unittest

from lab.exp011_manual import task_profile
from lab.exp010a_adaptive import choose
from lab.exp014_neutral_padding import (
    EXPECTED_IDS, MANIFEST, NUMBER, PADDING, audit, planned_calls,
    validate_manifest, variants,
)


def fixture():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


class NeutralPaddingAuditTests(unittest.TestCase):
    def test_manifest_predeclared_and_has_six_families(self):
        data = fixture()
        validate_manifest(data)
        self.assertEqual([c["id"] for c in data["cases"]], list(EXPECTED_IDS))
        self.assertEqual(sum(c["declared_steps"] == 1 for c in data["cases"]), 3)

    def test_padding_has_no_numeric_information(self):
        self.assertEqual(NUMBER.findall(PADDING), [])
        data = fixture()
        for case in data["cases"]:
            variants_by_length = variants(case["question"])
            for text in variants_by_length.values():
                self.assertEqual(NUMBER.findall(text), NUMBER.findall(case["question"]))

    def test_only_append_registered_neutral_sentence(self):
        data = fixture()
        for item in data["cases"]:
            base = item["question"]
            variants_by_length = variants(base)
            for text in variants_by_length.values():
                self.assertTrue(text.startswith(base))
                tail = text[len(base):].strip()
                self.assertFalse(tail.replace(PADDING, "").strip())

    def test_three_frozen_word_bands(self):
        for item in fixture()["cases"]:
            v = variants(item["question"])
            self.assertLess(len(v["short"].split()), 40)
            self.assertTrue(40 <= len(v["medium"].split()) < 50)
            self.assertGreaterEqual(len(v["long"].split()), 50)

    def test_adapter_is_unmodified_exp011_task_profile(self):
        for item in fixture()["cases"]:
            for name, text in variants(item["question"]).items():
                task = task_profile(text, item["id"] + "-" + name)
                self.assertEqual(task.budget, 2)
                self.assertFalse(task.mandatory_review)
                if name == "short":
                    self.assertFalse(task.parallelizable)
                    self.assertEqual(task.uncertainty, 0)
                if name == "medium":
                    self.assertTrue(task.parallelizable)
                    self.assertEqual(task.uncertainty, 0)
                if name == "long":
                    self.assertTrue(task.parallelizable)
                    self.assertEqual(task.uncertainty, 2)

    def test_route_flip_for_all_families_is_mechanical(self):
        result = audit(fixture())
        self.assertEqual(result["base_families"], 6)
        self.assertEqual(result["total_input_variants"], 18)
        self.assertEqual(result["route_changes_by_pair"], {
            "short_to_medium": 6, "medium_to_long": 6,
            "short_to_long": 6,
        })
        for family in result["families"]:
            self.assertEqual([x["route"] for x in family["variants"]],
                             ["single", "parallel", "review"])

    def test_cost_proxy_doubles_but_no_real_cost_measured(self):
        result = audit(fixture())
        self.assertEqual(result["planned_role_calls_by_variant"],
                         {"short": 6, "medium": 12, "long": 12})
        self.assertEqual(result["short_to_long_role_call_ratio"], 2)
        self.assertFalse(result["model_accuracy_or_latency_measured"])
        self.assertEqual(result["model_calls_executed"], 0)

    def test_report_is_deterministic(self):
        data = fixture()
        self.assertEqual(audit(data), audit(copy.deepcopy(data)))

    def test_cannot_call_author_category_a_measured_difficulty(self):
        result = audit(fixture())
        self.assertEqual(result["categories_author_declared_not_measured"],
                         {"one_declared_step": 3, "multiple_declared_steps": 3})
        self.assertFalse(result["cognitive_semantic_equivalence_proven"])
        self.assertFalse(result["future_model_superiority_proven"])
        self.assertTrue(result["results_mechanical_not_statistical"])

    def test_reject_added_case(self):
        data = fixture()
        data["cases"].append(copy.deepcopy(data["cases"][0]))
        with self.assertRaises(ValueError):
            audit(data)

    def test_reject_changed_id(self):
        data = fixture()
        data["cases"][0]["id"] = "alternative"
        with self.assertRaises(ValueError):
            validate_manifest(data)

    def test_reject_modified_padding(self):
        data = fixture()
        data["padding"] = "Changed instruction"
        with self.assertRaises(ValueError):
            audit(data)

    def test_reject_oracle_field(self):
        data = fixture()
        data["answer_key_included"] = True
        with self.assertRaises(ValueError):
            audit(data)

    def test_reject_base_question_already_long(self):
        data = fixture()
        data["cases"][0]["question"] += " " + PADDING * 6
        with self.assertRaises(ValueError):
            audit(data)

    def test_reject_category_claim_change(self):
        data = fixture()
        data["cases"][0]["declared_steps"] = 3
        with self.assertRaises(ValueError):
            audit(data)

    def test_planned_calls_are_not_real_model_invocations(self):
        self.assertEqual([planned_calls(r) for r in
                          ("blocked", "single", "parallel", "review")],
                         [0, 1, 2, 2])
        with self.assertRaises(ValueError):
            planned_calls("invented")

    def test_no_gold_or_answers_in_output(self):
        result = audit(fixture())
        self.assertNotIn("answer_key", json.dumps(result))
        self.assertFalse(result["model_accuracy_or_latency_measured"])
        for family in result["families"]:
            self.assertTrue(family["question_facts_preserved_as_numeric_tokens"])

    def test_durable_versioned_summary_matches_recomputed_routing(self):
        from lab.exp014_neutral_padding import ROOT
        expected = json.loads((ROOT / "results" / "exp014-routing-summary.json")
                              .read_text(encoding="utf-8"))
        actual = audit(fixture())
        for field in ("base_families", "total_input_variants",
                      "route_counts", "route_changes_by_pair",
                      "planned_role_calls_by_variant",
                      "short_to_long_role_call_ratio", "model_calls_executed"):
            self.assertEqual(expected[field], actual[field], field)
        self.assertFalse(expected["real_model_accuracy_measured"])
        self.assertFalse(expected["statistical_improvement_proven"])

    def test_router_selection_directly_matches_source(self):
        for case in fixture()["cases"]:
            for name, q in variants(case["question"]).items():
                profile = task_profile(q, case["id"] + "-" + name)
                expected = {"short": "single", "medium": "parallel",
                            "long": "review"}[name]
                self.assertEqual(choose(profile, "adaptive"), expected)


if __name__ == "__main__":
    unittest.main()
