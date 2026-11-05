"""EXP-018: verify a frozen, complete and non-model natural-language routing audit."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from lab.exp014_neutral_padding import NUMBER
from lab.exp017_conservative import POLICIES, STATES, git_blob
from lab.exp018_natural_coverage import (
    CATEGORIES, FROZEN_MANIFEST_BLOB, MANIFEST_PATH, TRANSFORMS,
    VARIANTS, WORD_VARIANT_GROUPS, audit, load_manifest, make_variants,
    summary, validate_manifest,
)


class TestExp018NaturalCoverage(unittest.TestCase):
    def test_frozen_manifest_exact_bytes(self):
        self.assertEqual(git_blob(MANIFEST_PATH.read_bytes()), FROZEN_MANIFEST_BLOB)
        self.assertEqual(load_manifest()["experiment"], "EXP-018")

    def test_mutated_file_rejected_by_pinned_blob(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "changed.json"
            path.write_bytes(MANIFEST_PATH.read_bytes().replace(b"A baker", b"A bakerX"))
            with self.assertRaisesRegex(ValueError, "blob changed"):
                load_manifest(path)

    def test_rejects_changed_manifest_and_missing_cases(self):
        data = load_manifest()
        data["cases"].pop()
        with self.assertRaises(ValueError):
            validate_manifest(data)
        data = load_manifest()
        data["answer_key_included"] = True
        with self.assertRaises(ValueError):
            validate_manifest(data)

    def test_rejects_dropped_word_mapping(self):
        data = load_manifest()
        data["cases"][0]["digit_spellings"].pop("18")
        with self.assertRaises(ValueError):
            validate_manifest(data)

    def test_rejects_wrong_intent_annotation(self):
        data = load_manifest()
        data["cases"][0]["author_math_intent"] = False
        with self.assertRaises(ValueError):
            validate_manifest(data)

    def test_six_categories_four_cases_each(self):
        data = load_manifest()
        self.assertEqual(len(data["cases"]), 24)
        counts = {c: sum(x["category"] == c for x in data["cases"]) for c in CATEGORIES}
        self.assertEqual(counts, {c: 4 for c in CATEGORIES})
        self.assertEqual(sum(x["author_math_intent"] for x in data["cases"]), 20)

    def test_new_not_borrowed_from_exp016(self):
        from lab.exp016_routing_stress import load_frozen_manifest
        former = {x["question"] for x in load_frozen_manifest()["cases"]}
        latest = {x["question"] for x in load_manifest()["cases"]}
        self.assertTrue(former.isdisjoint(latest))

    def test_unmarked_suffixes_do_not_add_digit_tokens(self):
        data = load_manifest()
        for case in data["cases"]:
            texts = make_variants(case, data)
            for variant in ("polite", "background", "embedded_format"):
                self.assertTrue(texts[variant].startswith(case["question"] + " "))
                self.assertEqual(NUMBER.findall(texts[variant]),
                                 NUMBER.findall(case["question"]))

    def test_paraphrases_were_written_not_synthesized_from_router(self):
        data = load_manifest()
        for case in data["cases"]:
            texts = make_variants(case, data)
            self.assertEqual(texts["paraphrase"], case["paraphrase"])
            self.assertNotEqual(texts["paraphrase"], texts["base"])

    def test_digits_to_words_only_in_preregistered_groups(self):
        data = load_manifest()
        n = 0
        for case in data["cases"]:
            texts = make_variants(case, data)
            if case["category"] in WORD_VARIANT_GROUPS:
                self.assertIn("number_words", texts)
                self.assertTrue(NUMBER.findall(texts["base"]))
                self.assertFalse(NUMBER.findall(texts["number_words"]))
                n += 1
            else:
                self.assertNotIn("number_words", texts)
        self.assertEqual(n, 16)

    def test_complete_136_entries_per_policy(self):
        report = audit(load_manifest())
        self.assertEqual(report["base_cases"], 24)
        self.assertEqual(report["variants_per_policy"], 136)
        self.assertEqual(tuple(report["policies"]), POLICIES)
        for policy in POLICIES:
            totals = {v: sum(report["route_counts_by_variant"][policy][v].values())
                      for v in VARIANTS}
            self.assertEqual(totals, {"base": 24, "paraphrase": 24, "polite": 24,
                                      "background": 24, "embedded_format": 24,
                                      "number_words": 16})

    def test_pair_denominators_and_invalid_distinction(self):
        report = audit(load_manifest())
        for p in POLICIES:
            for variant in TRANSFORMS:
                counts = report["pair_counts"][p][variant]
                self.assertEqual(counts["total"], 16 if variant == "number_words" else 24)
                self.assertEqual(counts["total"], sum(
                    counts[k] for k in ("unchanged", "changed", "invalid_base",
                                        "invalid_variant")
                ))
        self.assertEqual(report["route_counts_by_variant"]
                         ["candidate_content"]["number_words"].get("invalid_input"), 16)

    def test_all_and_base_metrics_have_fixed_intent_denominators(self):
        report = audit(load_manifest())
        for policy in POLICIES:
            base = report["base_and_all_metrics"][policy]["base"]
            all_ = report["base_and_all_metrics"][policy]["all"]
            self.assertEqual((base["total"], base["author_math_intent"],
                              base["author_nonmath_intent"]), (24, 20, 4))
            self.assertEqual((all_["total"], all_["author_math_intent"],
                              all_["author_nonmath_intent"]), (136, 116, 20))
            self.assertLessEqual(base["author_math_without_role"], 20)
            self.assertLessEqual(base["author_nonmath_assigned_role"], 4)
            self.assertEqual(base["assigned_role"] + base["abstained_uncertain_or_unsupported"]
                             + base["invalid_input"] + base["blocked"], 24)

    def test_budget_rows_never_drop_cases(self):
        report = audit(load_manifest())
        for policy in POLICIES:
            for budget in ("0", "1", "2"):
                rows = report["budget_base_routes"][policy][budget]
                self.assertEqual(sum(rows.values()), 24)
                self.assertTrue(set(rows).issubset(set(STATES)))

    def test_invalid_does_not_mean_zero_real_cost(self):
        report = audit(load_manifest())
        for case in report["cases"]:
            for item in case["variants"]:
                for policy in POLICIES:
                    decision = item["routes"][policy]
                    if decision["status"] == "invalid_input":
                        self.assertIsNone(decision["planned_calls"])

    def test_generated_report_never_claims_model_evaluation(self):
        report = audit(load_manifest())
        self.assertEqual(report["model_calls_executed"], 0)
        self.assertFalse(report["model_accuracy_latency_cost_measured"])
        self.assertFalse(report["blind_representative_or_independent"])
        self.assertFalse(report["semantic_equivalence_for_llms_proven"])
        self.assertTrue(report["categories_author_labeled_not_intent_oracle"])
        self.assertNotIn("answer_key", json.dumps(report))

    def test_deterministic_and_pinned_summary(self):
        m = load_manifest()
        actual = audit(m)
        self.assertEqual(actual, audit(copy.deepcopy(m)))
        self.assertEqual(summary(actual)["input_manifest_git_blob"], FROZEN_MANIFEST_BLOB)


if __name__ == "__main__":
    unittest.main()
