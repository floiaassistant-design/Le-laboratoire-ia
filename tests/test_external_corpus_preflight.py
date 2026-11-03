"""Offline tests of source metadata; never contact GitHub in unittest."""
import copy
import unittest
from pathlib import Path

from lab.external_corpus_preflight import (
    inspect_case, load_manifest, run, validate_manifest
)

class ExternalPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest()

    def test_manifest_well_formed(self):
        self.assertEqual(len(self.manifest["cases"]), 2)
        self.assertEqual(self.manifest["dataset"]["redistribution_authorized"], False)

    def test_manifest_all_commits_pinned(self):
        for bug in self.manifest["cases"]:
            self.assertEqual(len(bug["buggy"]), 40)
            self.assertEqual(len(bug["fixed"]), 40)

    def test_reject_unpinned_buggy_commit(self):
        x = copy.deepcopy(self.manifest)
        x["cases"][0]["buggy"] = "main"
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_reject_unlicensed_dataset_copy(self):
        x = copy.deepcopy(self.manifest)
        x["dataset"]["redistribution_authorized"] = True
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_reject_ambiguous_test_file(self):
        x = copy.deepcopy(self.manifest)
        x["cases"][0]["test_path"] = "../LICENSE"
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_reject_duplicate_case(self):
        x = copy.deepcopy(self.manifest)
        x["cases"][1]["id"] = "PySnooper-1"
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_reject_claim_of_execution(self):
        x = copy.deepcopy(self.manifest)
        x["study"]["source_executed"] = True
        with self.assertRaises(ValueError):
            validate_manifest(x)

    def test_offline_mode_no_network(self):
        from unittest.mock import patch
        with patch("lab.external_corpus_preflight._retrieve",
                   side_effect=AssertionError("Unexpected network")):
            result = run(self.manifest, online=False)
        self.assertFalse(result["metadata_verified"])
        self.assertEqual(result["bugs_executed"], 0)
        self.assertEqual(result["scored_cases"], 0)

    def test_source_error_never_means_success(self):
        from unittest.mock import patch
        with patch("lab.external_corpus_preflight._retrieve",
                   side_effect=OSError("Mocked network failure")):
            result = inspect_case(self.manifest["cases"][0])
        self.assertFalse(result["source_verified"])

if __name__ == "__main__":
    unittest.main()
