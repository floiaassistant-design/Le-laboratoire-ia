import unittest

from lab.pysnooper_unicode_smoke import (
    SUCCESS_MARKER, OLD_FAILURE, success_evidence, PROBE
)

class PySnooperSmokeTests(unittest.TestCase):
    def test_only_specific_error_counts(self):
        result = success_evidence(
            {"returncode": 1, "stderr": "ImportError: blocked"},
            {"returncode": 0, "stdout": SUCCESS_MARKER})
        self.assertFalse(result["bug_reproduced"])

    def test_fixed_must_pass(self):
        result = success_evidence(
            {"returncode": 1, "stderr": OLD_FAILURE},
            {"returncode": 1, "stdout": ""})
        self.assertFalse(result["bug_reproduced"])

    def test_specific_old_fail_and_fixed_success(self):
        result = success_evidence(
            {"returncode": 1, "stderr": OLD_FAILURE},
            {"returncode": 0, "stdout": SUCCESS_MARKER})
        self.assertTrue(result["bug_reproduced"])

    def test_probe_uses_only_unicode_assertion(self):
        self.assertIn("locale.getpreferredencoding", PROBE)
        self.assertIn("pysnooper.snoop", PROBE)
        self.assertNotIn("pip install", PROBE)

if __name__ == "__main__":
    unittest.main()
