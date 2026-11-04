"""Offline EXP-009D-C tests: no PyPI, no software under test."""
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest

from lab.exp009d_psutil_alternatives import (
    CANDIDATES, CASE_IDS, OTHER_PINS,
    download_binary, environment, evaluate, validate_plan,
)


def blocked(argv, **kw):
    return SimpleNamespace(returncode=1)


def ok(argv, **kw):
    directory = Path(argv[argv.index("--dest") + 1])
    wheel = directory / "psutil-5.8.0-py3-none-any.whl"
    wheel.write_bytes(b"synthetic binary data")
    return SimpleNamespace(returncode=0)


class AlternativeTests(unittest.TestCase):
    def test_source_predeclared_before_probe(self):
        self.assertEqual(validate_plan()["experiment"], "EXP-009D-C")

    def test_three_alternatives_fixed(self):
        self.assertEqual(CANDIDATES,
                         ["psutil==5.7.3", "psutil==5.8.0", "psutil==5.9.8"])

    def test_original_cases_preserved(self):
        self.assertEqual(CASE_IDS,
                         ["thefuck-1", "thefuck-2", "thefuck-3"])

    def test_other_pins_unchanged(self):
        self.assertEqual(OTHER_PINS, ["pyte==0.8.0",
                                      "pytest==5.4.3", "pexpect==4.8.0"])

    def test_other_versions_or_commands_rejected(self):
        with self.assertRaises(ValueError):
            download_binary(["psutil==8.0.0"], resolve_dependencies=False,
                            runner=blocked)

    def test_minimal_environment_omits_secrets(self):
        env = environment("/tmp/safe")
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("PYTHONPATH", env)
        self.assertNotIn("PIP_INDEX_URL", env)

    def test_single_wheel_is_not_an_install(self):
        result = download_binary(["psutil==5.8.0"],
                                 resolve_dependencies=False, runner=ok)
        self.assertEqual(result["status"], "wheels_downloaded_not_installed")
        self.assertEqual(result["wheel_count"], 1)
        self.assertFalse(result["package_installed"])
        self.assertFalse(result["upstream_code_executed"])

    def test_direct_probe_disables_deps(self):
        observed = []
        def capture(argv, **kw):
            observed.extend(argv)
            return SimpleNamespace(returncode=1)
        download_binary(["psutil==5.7.3"],
                        resolve_dependencies=False, runner=capture)
        self.assertIn("--no-deps", observed)
        self.assertIn("--only-binary=:all:", observed)
        self.assertNotIn("install", observed)

    def test_combined_probe_includes_transitives(self):
        observed = []
        def capture(argv, **kw):
            observed.extend(argv)
            return SimpleNamespace(returncode=1)
        download_binary(["psutil==5.8.0"] + OTHER_PINS,
                        resolve_dependencies=True, runner=capture)
        self.assertNotIn("--no-deps", observed)
        self.assertIn("--only-binary=:all:", observed)

    def test_failed_download_preserves_blocker(self):
        x = download_binary(["psutil==5.7.3"],
                            resolve_dependencies=False, runner=blocked)
        self.assertEqual(x["blocker"], "binary_download_or_resolution_failed")
        self.assertEqual(x["wheels"], [])

    def test_timeout_does_not_leak_error(self):
        def timeout(argv, **kw):
            raise subprocess.TimeoutExpired("private URL", 1)
        x = download_binary(["psutil==5.8.0"],
                            resolve_dependencies=False, runner=timeout)
        self.assertEqual(x["blocker"], "download_timeout")
        self.assertNotIn("private URL", json.dumps(x))

    def test_wrong_python_minor_never_runs_download(self):
        x = evaluate(python_minor="3.8", runner=blocked)
        self.assertEqual(x["classification"], "invalid_python_minor")
        self.assertEqual(x["candidate_probes"], [])

    def test_all_failed_candidates_do_not_change_history(self):
        x = evaluate(python_minor="3.7", runner=blocked)
        self.assertEqual(x["classification"],
                         "no_predeclared_alternative_direct_wheel")
        self.assertEqual(len(x["candidate_probes"]), 3)
        self.assertIsNone(x["selected_candidate"])
        self.assertFalse(x["semantics_equivalent_to_original"])

    def test_choose_first_success_in_predeclared_order(self):
        def fake(argv, **kw):
            # 5.7.3 blocked; 5.8.0 and 5.9.8 available.
            if "psutil==5.7.3" in argv:
                return SimpleNamespace(returncode=1)
            return ok(argv, **kw)
        x = evaluate(python_minor="3.7", runner=fake)
        self.assertEqual(x["selected_candidate"], "psutil==5.8.0")
        self.assertEqual(x["classification"],
                         "alternate_complete_binary_set_downloaded_not_installed")
        self.assertIsNone(x["policy_scores"])
        self.assertEqual(x["upstream_tests_executed"], 0)

    def test_complete_binary_resolution_can_still_fail(self):
        def fake(argv, **kw):
            if "--no-deps" in argv:
                return ok(argv, **kw)
            return SimpleNamespace(returncode=1)
        x = evaluate(python_minor="3.7", runner=fake)
        self.assertEqual(x["classification"],
                         "alternate_combined_resolution_blocked")
        self.assertEqual(x["selected_candidate"], "psutil==5.7.3")
        self.assertFalse(x["environment_installation_proven"])


if __name__ == "__main__":
    unittest.main()
