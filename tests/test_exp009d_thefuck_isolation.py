"""Offline tests of post-hoc TheFuck wheel blocker isolation. No network."""
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest

from lab.exp009d_thefuck_isolation import (
    REQUIRED_CASE_IDS, probe_all, probe_one,
    sanitized_environment, validate_source,
)


def failed(argv, **kw):
    return SimpleNamespace(returncode=1)


def succeeds(argv, **kw):
    output = Path(argv[argv.index("--dest") + 1])
    name = argv[-1].split("==")[0].replace("-", "_")
    version = argv[-1].split("==")[1]
    (output / (name + "-" + version + "-py3-none-any.whl")).write_bytes(b"wheel")
    return SimpleNamespace(returncode=0)


class IsolationTests(unittest.TestCase):
    def test_preselected_source_unchanged(self):
        self.assertEqual(validate_source(), [
            "psutil==5.6.7", "pyte==0.8.0",
            "pytest==5.4.3", "pexpect==4.8.0",
        ])

    def test_all_three_historical_cases_preserved(self):
        self.assertEqual(REQUIRED_CASE_IDS, [
            "thefuck-1", "thefuck-2", "thefuck-3"])

    def test_unknown_pin_disallowed(self):
        with self.assertRaises(ValueError):
            probe_one("pytest==99.0", runner=failed)

    def test_credentials_never_passed_to_pip(self):
        env = sanitized_environment("/tmp/test")
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("PIP_INDEX_URL", env)
        self.assertNotIn("PYTHONPATH", env)

    def test_offline_failure_is_a_blocker_not_a_detection(self):
        observed = probe_one("psutil==5.6.7", runner=failed)
        self.assertEqual(observed["status"], "blocked")
        self.assertEqual(observed["blocker"],
                         "binary_only_no_deps_download_failed")
        self.assertFalse(observed["dependencies_installed"])

    def test_binary_download_does_not_install(self):
        observed = probe_one("pyte==0.8.0", runner=succeeds)
        self.assertEqual(observed["status"], "single_wheel_downloaded")
        self.assertEqual(len(observed["sha256"]), 64)
        self.assertFalse(observed["upstream_imported"])

    def test_probe_requires_no_deps_and_only_binary(self):
        args_seen = []
        def capture(argv, **kw):
            args_seen.extend(argv)
            return SimpleNamespace(returncode=1)
        probe_one("pytest==5.4.3", runner=capture)
        self.assertIn("--no-deps", args_seen)
        self.assertIn("--only-binary=:all:", args_seen)
        self.assertNotIn("install", args_seen)

    def test_unexpected_file_blocks(self):
        def malicious(argv, **kw):
            d = Path(argv[argv.index("--dest") + 1])
            (d / "not-wheel.exe").write_bytes(b"anything")
            return SimpleNamespace(returncode=0)
        self.assertEqual(probe_one("pytest==5.4.3", runner=malicious)
                         ["blocker"], "wheel_metadata_missing_or_unexpected")

    def test_timeout_sanitized(self):
        def timeout(argv, **kw):
            raise subprocess.TimeoutExpired(cmd="token PRIVATE", timeout=1)
        result = probe_one("pytest==5.4.3", runner=timeout)
        self.assertEqual(result["blocker"], "download_timeout")
        self.assertNotIn("PRIVATE", json.dumps(result))

    def test_incorrect_python_minor_rejects_probe(self):
        report = probe_all(runner=failed, python_minor="3.8")
        self.assertEqual(report["classification"], "invalid_python_minor")
        self.assertEqual(report["individual_probes"], [])

    def test_four_direct_blockers_preserved(self):
        report = probe_all(runner=failed, python_minor="3.7")
        self.assertEqual(report["classification"],
                         "at_least_one_direct_binary_download_blocked")
        self.assertEqual(len(report["individual_probes"]), 4)
        self.assertEqual(report["policy_scores_generated"], 0)
        self.assertEqual(report["cases_preserved"], REQUIRED_CASE_IDS)

    def test_all_direct_wheels_does_not_imply_full_resolved(self):
        report = probe_all(runner=succeeds, python_minor="3.7")
        self.assertEqual(report["classification"],
                         "all_direct_binaries_available_full_resolution_still_blocked")
        self.assertFalse(report["environment_complete"])
        self.assertEqual(report["upstream_tests_executed"], 0)


if __name__ == "__main__":
    unittest.main()
