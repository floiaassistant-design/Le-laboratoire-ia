"""EXP-009B candidate manifest: structural verification only (no network)."""
import copy
import json
import unittest
from lab.exp009b_candidates import MANIFEST, validate_manifest


def sample():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


class CandidatePreflightTests(unittest.TestCase):
    def test_twelve_candidates_four_projects(self):
        x = validate_manifest(sample())
        self.assertEqual((x["candidate_count"], x["project_count"]), (12, 4))
        self.assertEqual(x["tests_executed"], 0)

    def test_bad_origin_rejected(self):
        x = sample()
        x["source"]["sha"] = "0" * 40
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_old_project_rejected(self):
        x = sample()
        x["cases"][0]["project"] = "tornado"
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_duplicate_case_rejected(self):
        x = sample()
        x["cases"][0]["id"] = x["cases"][1]["id"]
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_missing_sha_rejected(self):
        x = sample()
        x["cases"][0]["fixed"] = "bad"
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_missing_parent_verified_rejected(self):
        x = sample()
        x["cases"][0]["commit_parent_verified"] = False
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_unsafe_test_path_rejected(self):
        x = sample()
        x["cases"][0]["test_file"] = "../.secrets.py"
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_no_fake_executed_results(self):
        x = sample()
        x["cases"][0]["test_suite_execution"] = "passed"
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_score_field_rejected(self):
        x = sample()
        x["cases"][0]["score"] = 1
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_licence_verification_not_claimed(self):
        x = sample()
        x["projects"]["black"]["license_each_revision_pending"] = False
        with self.assertRaises(ValueError):
            validate_manifest(x)


if __name__ == "__main__":
    unittest.main()
