import unittest
from lab.real_bug_priority import (policy_orders, method_features,
                                   exact_random_hit, validate_manifest,
                                   RecordingResult, child_run, _bucket)


class RealBugPriorityTests(unittest.TestCase):
    def test_exact_probability_basic(self):
        self.assertAlmostEqual(exact_random_hit(12,1,1),1/12)
        self.assertEqual(exact_random_hit(12,0,12),0)
        self.assertEqual(exact_random_hit(12,1,12),1)
        self.assertEqual(exact_random_hit(4,4,1),1)

    def test_exact_probability_invalid(self):
        with self.assertRaises(ValueError):
            exact_random_hit(0,0,0)
        with self.assertRaises(ValueError):
            exact_random_hit(2,3,1)

    def test_policy_no_results_required(self):
        ids=["a.X.test_a","a.X.test_b","a.X.test_c"]
        features={ids[0]:frozenset(["a"]),ids[1]:frozenset(["b"]),
                  ids[2]:frozenset(["b","c"])}
        a=policy_orders(ids,features,5)
        self.assertEqual(set(a),{"lexical","seeded_random","structural_diversity"})
        for order in a.values():
            self.assertEqual(set(order),set(ids))

    def test_policy_reproducible(self):
        ids=["a.B.test_"+str(i) for i in range(7)]
        tags={x:frozenset([x[-1]]) for x in ids}
        self.assertEqual(policy_orders(ids,tags,20261103),
                         policy_orders(ids,tags,20261103))

    def test_order_input_independent(self):
        ids=["z.A.test_a","z.B.test_b","a.C.test_c"]
        tags={x:frozenset([x.split(".")[-1]]) for x in ids}
        self.assertEqual(policy_orders(ids,tags,1),
                         policy_orders(list(reversed(ids)),tags,1))

    def test_duplicate_cases_fail_closed(self):
        with self.assertRaises(ValueError):
            policy_orders(["same","same"],{"same":frozenset()},1)

    def test_missing_features_fail_closed(self):
        with self.assertRaises(ValueError):
            policy_orders(["a","b"],{"a":frozenset()},1)

    def test_method_features_from_static_code(self):
        source="class TestA:\n    def test_hello(self):\n        assert True\n"
        features=method_features(source,["x.TestA.test_hello"])
        self.assertIn("assert:1",features["x.TestA.test_hello"])
        self.assertNotIn("no_direct_ast_definition",features["x.TestA.test_hello"])

    def test_missing_ast_never_fabricates_test(self):
        features=method_features("x=1",["a.B.test_hello"])
        self.assertIn("no_direct_ast_definition",features["a.B.test_hello"])

    def test_recording_result(self):
        class Stub(unittest.TestCase):
            def test_ok(self): self.assertTrue(True)
        r=RecordingResult()
        s=Stub("test_ok")
        s.run(r)
        self.assertEqual(r.status[s.id()],"pass")

    def test_bucket(self):
        self.assertEqual([_bucket(x) for x in (0,1,2,4,8)],
                         ["0","1","2-3","4-7","8+"])

    def test_manifest_preserves_case_order(self):
        from lab.real_bug_priority import manifest
        m=manifest()
        self.assertEqual([c["id"] for c in m["cases"]],
                         ["youtube-dl-1","tornado-1"])
        self.assertEqual(m["budgets"],[1,3,6,12])

    def test_reject_changed_case(self):
        import copy
        from lab.real_bug_priority import manifest
        m=copy.deepcopy(manifest())
        m["cases"][0]["repo"]="fake/repo"
        with self.assertRaises(ValueError):
            validate_manifest(m)


if __name__=="__main__":
    unittest.main()
