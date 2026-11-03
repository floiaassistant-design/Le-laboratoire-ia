"""Only synthetic/offline tests; upstream source is not needed here."""
import copy
import unittest

from lab.tqdm_start_smoke import load_manifest, validate_manifest, parse_probe, verdict, MARKER

class TqdmSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest()

    def test_manifest_pinned(self):
        self.assertEqual(len(self.manifest["case"]["buggy_commit"]), 40)
        self.assertEqual(len(self.manifest["case"]["fixed_commit"]), 40)

    def test_reject_noncommit(self):
        doc = copy.deepcopy(self.manifest)
        doc["case"]["buggy_commit"] = "main"
        with self.assertRaises(ValueError):
            validate_manifest(doc)

    def test_reject_changed_target(self):
        doc = copy.deepcopy(self.manifest)
        doc["case"]["start"] = 0
        with self.assertRaises(ValueError):
            validate_manifest(doc)

    def test_reject_performance_claim(self):
        doc = copy.deepcopy(self.manifest)
        doc["interpretation"]["policy_comparison"] = True
        with self.assertRaises(ValueError):
            validate_manifest(doc)

    def test_parse_probe(self):
        val = parse_probe('TQDM_PROBE={"indexes":[0,1,2],"values":["a","b","c"]}\n')
        self.assertEqual(val["indexes"], [0,1,2])
        self.assertIsNone(parse_probe("ImportError: unavailable"))

    def test_semantic_mismatch_then_fix(self):
        old={"returncode":0,"parsed":{"indexes":[0,1,2],"values":["a","b","c"]}}
        new={"returncode":0,"parsed":{"indexes":[42,43,44],"values":["a","b","c"]}}
        self.assertTrue(verdict(old,new,self.manifest)["bug_reproduced"])

    def test_import_error_never_counts_as_bug(self):
        old={"returncode":1,"parsed":None,"stderr_tail":"ImportError"}
        new={"returncode":0,"parsed":{"indexes":[42,43,44],"values":["a","b","c"]}}
        self.assertFalse(verdict(old,new,self.manifest)["bug_reproduced"])

    def test_malformed_correct_result_rejected(self):
        old={"returncode":0,"parsed":{"indexes":[0,1,2],"values":["a","b","c"]}}
        new={"returncode":0,"parsed":{"indexes":[42,43,44],"values":["a","wrong","c"]}}
        self.assertFalse(verdict(old,new,self.manifest)["bug_reproduced"])

if __name__=="__main__":
    unittest.main()
