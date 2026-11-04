"""EXP-009B offline synthetic fixtures; no third-party code and no model."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from lab.exception_diagnostics import (
    DiagnosticResult, capture_suite, describe_exception, phase_for_unittest,
    redacted_view, safe_identifier, MAX_PROJECT_FRAMES,
)

ROOT = Path(__file__).resolve().parents[1]


class DiagnosticsTests(unittest.TestCase):
    def obtain_error(self, func):
        try:
            func()
        except BaseException as exc:
            return exc, exc.__traceback__
        self.fail("Expected synthetic exception")

    def test_safe_type(self):
        self.assertEqual(safe_identifier("UnicodeEncodeError"), "UnicodeEncodeError")

    def test_unsafe_type_redacted(self):
        self.assertEqual(safe_identifier("a-secret@example.com"), "redacted_identifier")

    def test_long_name_redacted(self):
        self.assertEqual(safe_identifier("X" * 200), "redacted_identifier")

    def test_no_exception_message_or_locals_serialized(self):
        def bad():
            secret = "private-email@example.com"
            raise ValueError("private-email@example.com " + secret)
        exc, tb = self.obtain_error(bad)
        content = json.dumps(describe_exception(exc, tb, ROOT, "call"))
        self.assertEqual(json.loads(content)["exception_type"], "ValueError")
        self.assertNotIn("private-email", content)
        self.assertNotIn(str(ROOT), content)

    def test_only_relative_project_frames(self):
        exc, tb = self.obtain_error(lambda: 1 / 0)
        detail = describe_exception(exc, tb, ROOT, "call")
        self.assertTrue(detail["project_frames"])
        self.assertTrue(all(not x["file"].startswith("/") for x in detail["project_frames"]))

    def test_out_of_project_frames_excluded(self):
        exc, tb = self.obtain_error(lambda: 1 / 0)
        data = describe_exception(exc, tb, ROOT / "third_party", "call")
        self.assertEqual(data["project_frames"], [])

    def test_bounded_frames(self):
        def recursive(n):
            if not n:
                raise RuntimeError("secret")
            recursive(n-1)
        exc, tb = self.obtain_error(lambda: recursive(10))
        data = describe_exception(exc, tb, ROOT, "call")
        self.assertLessEqual(len(data["project_frames"]), MAX_PROJECT_FRAMES)

    def test_invalid_phase_rejected(self):
        exc, tb = self.obtain_error(lambda: 1 / 0)
        with self.assertRaises(ValueError):
            describe_exception(exc, tb, ROOT, "unapproved")

    def test_phase_unknown_without_unittest_frame(self):
        exc, tb = self.obtain_error(lambda: 1 / 0)
        self.assertEqual(phase_for_unittest(tb), "unknown")

    def test_unittest_call_exception_preserved_as_error(self):
        class Synthetic(unittest.TestCase):
            def test_business(self):
                raise LookupError("SECRET-TOKEN")
        result = capture_suite(unittest.TestSuite([Synthetic("test_business")]), ROOT)
        self.assertTrue(result["valid"])
        self.assertEqual(result["counts"], {"error": 1})
        detail = next(iter(result["exceptions"].values()))
        self.assertEqual(detail["exception_type"], "LookupError")
        self.assertEqual(detail["phase"], "call")
        self.assertNotIn("SECRET", json.dumps(result))

    def test_unittest_setup_failure_identified(self):
        class Synthetic(unittest.TestCase):
            def setUp(self):
                raise ValueError("SECRET")
            def test_business(self):
                self.fail("not called")
        result = capture_suite(unittest.TestSuite([Synthetic("test_business")]), ROOT)
        detail = next(iter(result["exceptions"].values()))
        self.assertEqual(detail["phase"], "setup")

    def test_unittest_teardown_failure_identified(self):
        class Synthetic(unittest.TestCase):
            def test_business(self):
                pass
            def tearDown(self):
                raise ValueError("SECRET")
        result = capture_suite(unittest.TestSuite([Synthetic("test_business")]), ROOT)
        detail = next(iter(result["exceptions"].values()))
        self.assertEqual(detail["phase"], "teardown")

    def test_assertion_kept_separate(self):
        class Synthetic(unittest.TestCase):
            def test_business(self):
                self.assertEqual(1, 2, "private")
        result = capture_suite(unittest.TestSuite([Synthetic("test_business")]), ROOT)
        self.assertEqual(result["counts"], {"fail": 1})
        self.assertEqual(next(iter(result["exceptions"].values()))["exception_type"],
                         "AssertionError")
        self.assertNotIn("private", json.dumps(result))

    def test_capture_rejects_empty_suite(self):
        self.assertFalse(capture_suite(unittest.TestSuite(), ROOT)["valid"])

    def test_focus_strips_all_non_focus_test_ids(self):
        report = {"valid": True, "collected": 2, "executed": 2,
                  "counts": {"pass": 1, "error": 1},
                  "statuses": {"approved.test": "error", "secret.test": "pass"},
                  "exceptions": {"approved.test": {"exception_type": "ValueError",
                          "phase": "call", "project_frames": []}}}
        filtered = redacted_view(report, {"approved.test"})
        self.assertEqual(list(filtered["focus"]), ["approved.test"])
        self.assertNotIn("secret.test", json.dumps(filtered))

    def test_missing_focus_reported(self):
        report = {"valid": True, "collected": 1, "executed": 1,
                  "counts": {"pass": 1}, "statuses": {"a": "pass"}, "exceptions": {}}
        self.assertEqual(redacted_view(report, {"b"})["missing_focus_count"], 1)

    def test_invalid_report_redacted(self):
        result = redacted_view({"valid": False, "reason": "collection_error"}, {"x"})
        self.assertEqual(result["reason"], "collection_error")
        self.assertNotIn("focus", result)


if __name__ == "__main__":
    unittest.main()
