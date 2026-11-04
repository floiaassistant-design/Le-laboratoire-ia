"""Pure tests of EXP-009B interpretation. No Git/network."""
import unittest
from lab.exp009b_qualification import CASES, assess


def case_(id_="youtube-dl-4"):
    return {"id": id_, "project": "youtube-dl",
            "test_file": "test/test_jsinterp.py"}


def report_(id_, status, *, ex=None, warnings=False):
    focus = {} if id_ is None else {id_: {"status": status, "exception": ex}}
    return {"valid": True, "collected": 12, "executed": 12,
            "counts": {status: 12}, "focus": focus,
            "stderr_warning_keyword_present": warnings}


class QualificationTests(unittest.TestCase):
    def test_four_frozen_cases_only(self):
        self.assertEqual(set(CASES),
                         {"youtube-dl-4", "tornado-2", "tornado-3", "cookiecutter-1"})

    def test_error_to_pass_is_not_confirmed_bug(self):
        target = CASES["youtube-dl-4"]
        detail = {"exception_type": "TypeError", "phase": "call",
                  "project_frames": [{"file": "youtube_dl/jsinterp.py",
                                      "function": "extract", "line": 12}]}
        buggy = report_(target, "error", ex=detail)
        fixed = report_(target, "pass")
        old = {"status_counts_buggy": buggy["counts"],
               "status_counts_fixed": fixed["counts"]}
        result = assess(case_(), old, buggy, fixed)
        self.assertEqual(result["classification"], "unattributed_differential_exception")
        self.assertTrue(result["source_code_frame_present"])
        self.assertNotIn("confirmed_bug", result)

    def test_missing_declared_id_is_blocked(self):
        target = CASES["youtube-dl-4"]
        buggy = report_(target, "error")
        fixed = report_(None, "pass")
        outcome = assess(case_(), {}, buggy, fixed)
        self.assertEqual(outcome["status"], "blocked")

    def test_new_status_does_not_rewrite_historical(self):
        target = CASES["youtube-dl-4"]
        buggy = report_(target, "pass")
        fixed = report_(target, "pass")
        old = {"status_counts_buggy": {"error": 1, "pass": 11},
               "status_counts_fixed": {"pass": 12}}
        result = assess(case_(), old, buggy, fixed)
        self.assertFalse(result["historical_status_counts_match"])
        self.assertEqual(result["classification"], "changed_or_unreproduced_not_attributed")

    def test_tornado_3_no_unfounded_negative_conclusion(self):
        case = {"id": "tornado-3", "project": "tornado",
                "test_file": "tornado/test/httpclient_test.py"}
        before = report_(None, "pass")
        after = report_(None, "pass")
        old = {"status_counts_buggy": {"pass": 48},
               "status_counts_fixed": {"pass": 48}}
        result = assess(case, old, before, after)
        self.assertEqual(result["classification"], "no_confirmed_witness_in_selected_suite")
        self.assertIn("cannot infer absence", result["caution"])


if __name__ == "__main__":
    unittest.main()
