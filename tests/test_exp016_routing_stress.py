"""EXP-016 checks that route reports are reproducible and never claim LLM results."""
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from lab.exp014_neutral_padding import NUMBER
from lab.exp015_content_router import STAGE
from lab.exp016_routing_stress import (
    FROZEN_MANIFEST_BLOB, GROUPS, MANIFEST_PATH, TRANSFORMS, VARIANTS,
    audit, git_blob, load_frozen_manifest, make_variants, summary,
    validate_manifest,
)


class TestExp016RoutingStress(unittest.TestCase):
    def test_frozen_blob_matches_registration(self):
        self.assertEqual(git_blob(MANIFEST_PATH.read_bytes()), FROZEN_MANIFEST_BLOB)
        self.assertEqual(load_frozen_manifest()["experiment"], "EXP-016")

    def test_rejects_change_to_exact_frozen_bytes(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "tampered.json"
            path.write_bytes(MANIFEST_PATH.read_bytes().replace(b"Iris", b"IRIS"))
            with self.assertRaisesRegex(ValueError, "altered"):
                load_frozen_manifest(path)

    def test_rejects_case_omission(self):
        corrupted = load_frozen_manifest()
        corrupted["cases"].pop()
        with self.assertRaises(ValueError):
            validate_manifest(corrupted)

    def test_rejects_changed_labels(self):
        corrupted = load_frozen_manifest()
        corrupted["cases"][0]["author_declared_steps"] = 3
        with self.assertRaises(ValueError):
            validate_manifest(corrupted)

    def test_rejects_changed_number_words(self):
        corrupted = load_frozen_manifest()
        corrupted["cases"][0]["number_words"].pop("14")
        with self.assertRaises(ValueError):
            validate_manifest(corrupted)

    def test_new_groups_and_pair_denominators(self):
        manifest = load_frozen_manifest()
        self.assertEqual(len(manifest["cases"]), 16)
        self.assertEqual({c["category"] for c in manifest["cases"]}, set(GROUPS))
        self.assertEqual(len(TRANSFORMS), 4)
        self.assertEqual(len(VARIANTS), 5)
        report = audit(manifest)
        self.assertEqual(report["base_families"], 16)
        self.assertEqual(report["total_variants_per_policy"], 68)
        for policy in report["policies"]:
            self.assertEqual([report["pair_counts"][policy][t]["total"] for t in TRANSFORMS],
                             [16, 16, 16, 4])

    def test_neutral_variant_has_same_digits_and_no_new_stage_marker(self):
        manifest = load_frozen_manifest()
        for case in manifest["cases"]:
            items = make_variants(case, manifest)
            base, neutral = items["base"], items["neutral_padding"]
            self.assertTrue(neutral.startswith(base))
            self.assertGreaterEqual(len(neutral.split()), 60)
            self.assertEqual(NUMBER.findall(base), NUMBER.findall(neutral))
            self.assertEqual(bool(STAGE.search(base)), bool(STAGE.search(neutral)))

    def test_word_variant_replaces_all_digit_literals(self):
        manifest = load_frozen_manifest()
        for case in manifest["cases"]:
            items = make_variants(case, manifest)
            self.assertTrue(NUMBER.findall(items["base"]))
            self.assertFalse(NUMBER.findall(items["number_words"]))
            self.assertNotEqual(items["base"], items["number_words"])

    def test_misleading_suffix_does_not_add_digits(self):
        manifest = load_frozen_manifest()
        for case in manifest["cases"]:
            items = make_variants(case, manifest)
            self.assertTrue(STAGE.search(items["misleading_stage"]))
            self.assertEqual(NUMBER.findall(items["base"]),
                             NUMBER.findall(items["misleading_stage"]))

    def test_connectorless_variant_only_for_four_marked_cases(self):
        manifest = load_frozen_manifest()
        for case in manifest["cases"]:
            items = make_variants(case, manifest)
            if case["category"] == "multistep_marked":
                self.assertIn("stage_removed", items)
                self.assertFalse(STAGE.search(items["stage_removed"]))
            else:
                self.assertNotIn("stage_removed", items)

    def test_invalid_word_question_distinct_from_blocked(self):
        report = audit(load_frozen_manifest())
        for policy in report["policies"]:
            for transform in TRANSFORMS:
                row = report["pair_counts"][policy][transform]
                self.assertEqual(row["total"], sum(row[k] for k in
                                 ("changed", "unchanged", "invalid_base", "invalid_variant")))
        candidate = report["pair_counts"]["candidate_content"]["number_words"]
        self.assertEqual(candidate["invalid_variant"], 16)
        self.assertEqual(candidate["unchanged"], 0)
        self.assertEqual(candidate["changed"], 0)
        self.assertEqual(report["route_counts"]["candidate_content"]["number_words"],
                         {"invalid_input": 16})

    def test_budget_outcomes_keep_all_sixteen_cases(self):
        report = audit(load_frozen_manifest())
        for policy in report["policies"]:
            for budget in ("0", "1", "2"):
                self.assertEqual(sum(report["budget_base_routes"][policy][budget].values()), 16)
            self.assertEqual(report["budget_base_routes"][policy]["0"],
                             {"blocked": 16})

    def test_structural_labels_are_not_answers_or_quality_scores(self):
        report = audit(load_frozen_manifest())
        self.assertEqual(report["models_called"], 0)
        self.assertTrue(report["categories_author_declared_not_validation"])
        self.assertFalse(report["answer_correctness_or_cost_measured"])
        self.assertFalse(report["blind_or_representative_sample"])
        self.assertFalse(report["semantic_equivalence_independently_verified"])
        self.assertNotIn("answer_key", json.dumps(report))
        self.assertNotIn("accuracy_score", json.dumps(summary(report)))

    def test_deterministic_audit_and_summary(self):
        manifest = load_frozen_manifest()
        one = audit(manifest)
        self.assertEqual(one, audit(copy.deepcopy(manifest)))
        self.assertEqual(summary(one)["source_manifest_git_blob_sha"],
                         FROZEN_MANIFEST_BLOB)


    def test_versioned_summary_matches_fresh_report_exactly(self):
        expected = json.loads(
            (MANIFEST_PATH.parent.parent / "results" / "exp016-routing-summary.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(expected, summary(audit(load_frozen_manifest())))


if __name__ == "__main__":
    unittest.main()
