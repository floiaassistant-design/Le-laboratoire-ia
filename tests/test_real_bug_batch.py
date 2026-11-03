"""EXP-008B: offline qualification and conservative scoring tests."""
from __future__ import annotations
import copy
import unittest
from lab import real_bug_batch as batch
from lab.real_bug_priority import policy_orders as original_policy_orders

class BatchExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=batch.load_manifest()

    def test_exactly_eight_prespecified_bugs(self):
        self.assertEqual([c["id"] for c in self.manifest["cases"]], [
            "youtube-dl-2","youtube-dl-3","youtube-dl-4",
            "tornado-2","tornado-3","tornado-4",
            "cookiecutter-1","cookiecutter-2"])

    def test_original_strategy_code_reused_unchanged(self):
        self.assertIs(batch.policy_orders, original_policy_orders)

    def test_frozen_seed_and_budgets(self):
        self.assertEqual(self.manifest["seed"],20261103)
        self.assertEqual(tuple(self.manifest["budgets"]),batch.BUDGETS)

    def test_all_commit_hashes_pinned(self):
        for c in self.manifest["cases"]:
            self.assertEqual(len(c["buggy"]),40)
            self.assertEqual(len(c["fixed"]),40)
            self.assertNotEqual(c["buggy"],c["fixed"])

    def test_reject_changed_bug_identity(self):
        m=copy.deepcopy(self.manifest)
        m["cases"][0]["id"]="youtube-dl-1"
        with self.assertRaises(ValueError): batch.validate_manifest(m)

    def test_reject_changed_strategy(self):
        m=copy.deepcopy(self.manifest)
        m["policies"].reverse()
        with self.assertRaises(ValueError): batch.validate_manifest(m)

    def test_reject_bad_sha(self):
        m=copy.deepcopy(self.manifest)
        m["cases"][0]["buggy"]="main"
        with self.assertRaises(ValueError): batch.validate_manifest(m)

    def test_reject_url_overwrite(self):
        m=copy.deepcopy(self.manifest)
        m["cases"][0]["url"]="https://malicious.example/repo.git"
        with self.assertRaises(ValueError): batch.validate_manifest(m)

    def test_reject_unsafe_test_path(self):
        m=copy.deepcopy(self.manifest)
        m["cases"][0]["test_file"]="../secret.py"
        with self.assertRaises(ValueError): batch.validate_manifest(m)

    def test_features_unittest_found(self):
        c=self.manifest["cases"][0]
        f=batch.features_for_case(c, "class Foo:\n def test_thing(self):\n  assert True\n",
                                  ["test.x.Foo.test_thing"])
        self.assertIn("assert:1",f["test.x.Foo.test_thing"])

    def test_features_pytest_parameterization_shares_ast(self):
        c=self.manifest["cases"][-2]
        text="def test_many(x):\n assert x\n"
        ids=["tests/test_x.py::test_many[1]","tests/test_x.py::test_many[2]"]
        features=batch.features_for_case(c,text,ids)
        self.assertEqual(features[ids[0]],features[ids[1]])
        self.assertIn("assert:1",features[ids[0]])

    def test_score_detects_assertion_fail_but_not_environment_error(self):
        case=self.manifest["cases"][0]
        ids=["p.Test.test_1","p.Test.test_2","p.Test.test_3"]
        after={"ids":ids,"statuses":{x:"pass" for x in ids},
               "counts":{"pass":3},"wall_seconds":0.1}
        before={"ids":ids,"statuses":{ids[0]:"fail",ids[1]:"error",
                                     ids[2]:"pass"},
                "counts":{"fail":1,"error":1,"pass":1},"wall_seconds":0.2}
        result=batch.score_pair(case,before,after,
                                 "class Test:\n def test_1(self):\n  assert 1\n",2)
        self.assertEqual(result["revealing_assertion_test_count"],1)
        self.assertEqual(result["changed_error_not_counted"],1)

    def test_block_if_corrected_suite_contains_error(self):
        case=self.manifest["cases"][0]
        ids=["x.Test.test_bad"]
        before={"ids":ids,"statuses":{ids[0]:"fail"},"counts":{},"wall_seconds":0}
        after={"ids":ids,"statuses":{ids[0]:"error"},"counts":{},"wall_seconds":0}
        with self.assertRaises(ValueError):
            batch.score_pair(case,before,after,"class Test: pass",1)

    def test_block_if_identifiers_differ(self):
        case=self.manifest["cases"][0]
        before={"ids":["x"],"statuses":{"x":"fail"},"counts":{},"wall_seconds":0}
        after={"ids":["y"],"statuses":{"y":"pass"},"counts":{},"wall_seconds":0}
        with self.assertRaises(ValueError):
            batch.score_pair(case,before,after,"",1)

    def test_budget_clamped_for_small_suite(self):
        case=self.manifest["cases"][0]
        ids=["p.T.test_only"]
        before={"ids":ids,"statuses":{ids[0]:"fail"},"counts":{"fail":1},
                "wall_seconds":0}
        after={"ids":ids,"statuses":{ids[0]:"pass"},"counts":{"pass":1},
               "wall_seconds":0}
        x=batch.score_pair(case,before,after,"",1)
        self.assertEqual(x["effective_budgets"]["12"],1)
        self.assertEqual(x["exact_uniform_random_hit"]["12"],1)

    def test_no_real_bugs_are_used_by_policy_order(self):
        labels=["x.X.test_a","x.X.test_b","x.X.test_c"]
        features={k:frozenset([str(i)]) for i,k in enumerate(labels)}
        policies=batch.policy_orders(labels,features,20261103)
        self.assertEqual(set(policies),{"lexical","seeded_random",
                                        "structural_diversity"})

    def test_project_names_fixed(self):
        self.assertEqual(batch.PROJECTS,
                         ("youtube-dl","tornado","cookiecutter"))

    def test_manifest_rejects_missing_case(self):
        m=copy.deepcopy(self.manifest)
        m["cases"]=m["cases"][:-1]
        with self.assertRaises(ValueError): batch.validate_manifest(m)

if __name__=="__main__":
    unittest.main()
