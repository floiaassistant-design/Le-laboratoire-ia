"""Focused EXP-017 tests: input-only abstention, frozen corpus and legacy baselines."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from lab.exp017_conservative import (
    FROZEN_BLOB, MANIFEST, POLICIES, VARIANTS, audit, conservative_decision,
    decision_for, git_blob, load_manifest, summary, validate_manifest, variants,
)


class EXP017Checks(unittest.TestCase):
    def test_frozen_blob_and_case_structure(self):
        self.assertEqual(git_blob(MANIFEST.read_bytes()), FROZEN_BLOB)
        self.assertEqual(len(load_manifest()["cases"]), 16)

    def test_tampering_refused_by_git_blob(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "wrong.json"
            path.write_bytes(MANIFEST.read_bytes().replace(b"Compute 7", b"Compute 8"))
            with self.assertRaisesRegex(ValueError, "SHA mismatch"):
                load_manifest(path)

    def test_manifest_not_missing_cases(self):
        data = load_manifest()
        data["cases"].pop()
        with self.assertRaises(ValueError):
            validate_manifest(data)

    def test_manifest_order_must_match(self):
        data = load_manifest()
        data["cases"][0], data["cases"][1] = data["cases"][1], data["cases"][0]
        with self.assertRaises(ValueError):
            validate_manifest(data)

    def test_recognizes_one_step_digits_and_words(self):
        for text in ("Compute 7 plus 4.", "Calculate eighteen minus five.",
                     "Compute nine times three.", "Calculate 20 divided by 4."):
            with self.subTest(text=text):
                decision = conservative_decision(text)
                self.assertEqual(decision.status, "single")
                self.assertEqual(decision.calls_planned, 1)
                self.assertEqual(decision.reason, "exact_one_step")

    def test_recognizes_two_step_without_relying_on_word_then_only(self):
        for text in ("Compute 8 plus 3, then subtract 2.",
                     "Calculate twelve minus four, afterward add six.",
                     "Compute 5 times 3, next divide by three."):
            with self.subTest(text=text):
                self.assertEqual(conservative_decision(text).status, "needs_review")
                self.assertEqual(conservative_decision(text).calls_planned, 2)

    def test_format_word_then_is_not_arithmetic_stage(self):
        base = "Compute 7 plus 4."
        decorated = base + " Formatting instruction: include the word then in the margin."
        self.assertEqual(conservative_decision(decorated).status, "single")
        self.assertEqual(conservative_decision(decorated).annotation_count, 1)
        self.assertEqual(conservative_decision("Describe why a variable uses then.").status,
                         "unsupported")

    def test_tagged_neutral_does_not_change_decision(self):
        base = "Compute seven plus four."
        decorated = base + " Non-mathematical note: no extra numbers are given."
        self.assertEqual(conservative_decision(decorated).status, "single")
        self.assertEqual(conservative_decision(decorated).annotation_count, 1)

    def test_unmarked_note_cannot_be_silently_ignored(self):
        self.assertEqual(conservative_decision(
            "Compute 7 plus 4. Please answer then in uppercase."
        ).status, "uncertain")

    def test_unsupported_annotation_does_not_create_false_confidence(self):
        self.assertEqual(conservative_decision(
            "Compute 7 plus 4. Other paragraph. Formatting instruction: use then."
        ).status, "uncertain")

    def test_noncanonical_math_is_uncertain(self):
        for q in ("How many apples are left?", "Compute twenty-one plus three.",
                  "The invoice lists twelve units. What is the total?"):
            with self.subTest(q=q):
                self.assertEqual(conservative_decision(q).status, "uncertain")
                self.assertEqual(conservative_decision(q).calls_planned, 0)

    def test_non_arithmetic_is_unsupported(self):
        for q in ("Explain the formatting of a field.", "Describe a chart's background."):
            self.assertEqual(conservative_decision(q).status, "unsupported")

    def test_no_implicit_downgrade_when_budget_insufficient(self):
        for budget, status in ((0, "blocked_by_budget"), (1, "blocked_by_budget"),
                               (2, "needs_review")):
            d = conservative_decision("Compute 8 plus 3, then subtract 2.", budget=budget)
            self.assertEqual(d.status, status)
            self.assertEqual(d.calls_planned, 2 if budget == 2 else 0)
        self.assertEqual(conservative_decision("Compute 7 plus 4.", budget=0).status,
                         "blocked_by_budget")

    def test_invalid_questions_and_budget_are_rejected(self):
        for q in ("", 14, None, "a" * 6001):
            with self.assertRaises(ValueError):
                conservative_decision(q)
        for b in (-1, 3, True, 1.5):
            with self.assertRaises(ValueError):
                conservative_decision("Compute 7 plus 4.", budget=b)

    def test_complete_roster_is_48_for_each_policy(self):
        report = audit(load_manifest())
        self.assertEqual(report["entries_per_policy"], 48)
        self.assertEqual(report["case_count"], 16)
        self.assertEqual(tuple(report["policies"]), POLICIES)
        for policy in POLICIES:
            for name in VARIANTS:
                self.assertEqual(sum(report["route_counts"][policy][name].values()), 16)
            for variant in VARIANTS[1:]:
                pair = report["pair_counts"][policy][variant]
                self.assertEqual(pair["total"], 16)
                self.assertEqual(sum(pair[k] for k in
                                 ("unchanged", "changed", "invalid_base", "invalid_variant")), 16)

    def test_abstention_on_exp016_regression_is_recorded_not_hidden(self):
        report = audit(load_manifest())
        regression = report["exp016_public_development_regression"]
        self.assertEqual(sum(regression.values()), 16)
        self.assertFalse(report["independent_holdout"])
        self.assertFalse(report["quality_or_accuracy_measured"])

    def test_budget_counts_include_every_case_and_no_real_calls(self):
        report = audit(load_manifest())
        for policy in POLICIES:
            for b in ("0", "1", "2"):
                self.assertEqual(sum(report["base_budget_route_counts"][policy][b].values()), 16)
        self.assertEqual(report["models_called"], 0)
        self.assertFalse(report["generality_proven"])

    def test_report_repeatable_with_no_oracle(self):
        a = load_manifest()
        self.assertEqual(audit(a), audit(copy.deepcopy(a)))
        self.assertNotIn("answer_key", json.dumps(audit(a)))
        self.assertEqual(summary(audit(a))["input_manifest_git_blob"], FROZEN_BLOB)


    def test_versioned_results_equal_fresh_calculation(self):
        path = MANIFEST.parent.parent / "results" / "exp017-conservative-summary.json"
        expected = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(expected, summary(audit(load_manifest())))


if __name__ == "__main__":
    unittest.main()
