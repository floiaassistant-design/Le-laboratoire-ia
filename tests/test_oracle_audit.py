"""Offline tests: ensure EXP-009A never alters EXP-008B original oracle."""
import copy
import unittest
from lab.oracle_audit import audit_case, audit_reports


def fixture(case="youtube-dl-4", states=None):
    states=states or {"a":("error","pass"),"b":("pass","pass")}
    buggy={k:v[0] for k,v in states.items()}
    fixed={k:v[1] for k,v in states.items()}
    counts=lambda s:{x:list(s.values()).count(x) for x in sorted(set(s.values()))}
    d=sum(a=="fail" and b=="pass" for a,b in states.values())
    e=sum(a=="error" and b=="pass" for a,b in states.values())
    return {"case":case,"project":"youtube-dl","status":"evaluated",
            "result":{"all_test_statuses":{"buggy":buggy,"fixed":fixed},
                      "runtime_test_count":len(states),
                      "revealing_assertion_test_count":d,
                      "changed_error_not_counted":e,
                      "revealing_ids":[k for k,v in states.items()
                                       if v==("fail","pass")],
                      "buggy_status_counts":counts(buggy),
                      "fixed_status_counts":counts(fixed)}}


class OracleAuditTests(unittest.TestCase):
    def test_error_is_unattributed_signal_not_bug(self):
        x=audit_case(fixture())
        self.assertEqual(x["classification"],"unattributed_exception_to_pass")
        self.assertEqual(x["strict_assertion_fail_to_pass"],0)
        self.assertEqual(x["exception_error_to_pass_not_confirmed"],1)

    def test_both_pass_has_no_observed_difference(self):
        x=audit_case(fixture(states={"a":("pass","pass")}))
        self.assertEqual(x["classification"],"no_status_difference_in_chosen_test_file")

    def test_assertion_count_preserved(self):
        x=audit_case(fixture(states={"a":("fail","pass"),"b":("pass","pass")}))
        self.assertEqual(x["strict_assertion_fail_to_pass"],1)
        self.assertEqual(x["classification"],"strict_assertion_witness_exists")

    def test_mismatch_primary_score_rejected(self):
        e=fixture(states={"a":("error","pass")})
        e["result"]["revealing_assertion_test_count"]=1
        with self.assertRaises(ValueError):
            audit_case(e)

    def test_mismatch_error_count_rejected(self):
        e=fixture()
        e["result"]["changed_error_not_counted"]=0
        with self.assertRaises(ValueError):
            audit_case(e)

    def test_mismatch_ids_rejected(self):
        e=fixture()
        e["result"]["all_test_statuses"]["fixed"]["z"]="pass"
        with self.assertRaises(ValueError):
            audit_case(e)

    def test_mismatch_counts_rejected(self):
        e=fixture()
        e["result"]["fixed_status_counts"]={"pass":1}
        with self.assertRaises(ValueError):
            audit_case(e)

    def test_unknown_state_rejected(self):
        e=fixture()
        e["result"]["all_test_statuses"]["buggy"]["a"]="unknown"
        with self.assertRaises(ValueError):
            audit_case(e)

    def test_stable_hash_in_any_insertion_order(self):
        x=fixture(states={"a":("error","pass"),"b":("pass","pass")})
        y=fixture(states={"b":("pass","pass"),"a":("error","pass")})
        self.assertEqual(audit_case(x)["status_map_sha256_buggy"],
                         audit_case(y)["status_map_sha256_buggy"])

    def test_blocked_preserved_without_false_zero(self):
        x=audit_case({"case":"tornado-3","project":"tornado",
                      "status":"blocked","reason":"setup_error"})
        self.assertFalse(x["oracle_audited"])
        self.assertNotIn("strict_assertion_fail_to_pass",x)

    def test_all_reports_need_correct_experiment(self):
        with self.assertRaises(ValueError):
            audit_reports([{"experiment":"other","project":"youtube-dl",
                            "cases":[],"declared_case_count":0}])

    def test_duplicate_case_rejected(self):
        e=fixture()
        raw={"experiment":"EXP-008B","project":"youtube-dl",
             "cases":[e,e],"declared_case_count":2,
             "evaluated_count":2,"blocked_count":0}
        with self.assertRaises(ValueError):
            audit_reports([raw])

    def test_requires_all_eight_when_specified(self):
        e=fixture()
        raw={"experiment":"EXP-008B","project":"youtube-dl",
             "cases":[e],"declared_case_count":1,
             "evaluated_count":1,"blocked_count":0}
        with self.assertRaises(ValueError):
            audit_reports([raw],require_complete=True)

    def test_partial_project_audit(self):
        e=fixture()
        raw={"experiment":"EXP-008B","project":"youtube-dl",
             "cases":[e],"declared_case_count":1,
             "evaluated_count":1,"blocked_count":0}
        a=audit_reports([raw])
        self.assertEqual(a["target_error_to_pass_case_count"],1)
        self.assertFalse(a["error_to_pass_is_confirmed_bug"])

    def test_duplicate_project_rejected(self):
        e=fixture()
        raw={"experiment":"EXP-008B","project":"youtube-dl",
             "cases":[e],"declared_case_count":1,
             "evaluated_count":1,"blocked_count":0}
        with self.assertRaises(ValueError):
            audit_reports([raw,raw])

    def test_counts_preserved_after_auditing(self):
        e=fixture()
        original=copy.deepcopy(e)
        audit_case(e)
        self.assertEqual(e,original)

    def test_no_status_difference_does_not_imply_no_bug(self):
        e=fixture(case="tornado-3",states={"a":("pass","pass")})
        x=audit_case(e)
        self.assertEqual(x["observed_transition_count"],0)
        self.assertNotIn("no_bug_exists",x)


if __name__=="__main__":
    unittest.main()
