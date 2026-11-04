"""EXP-009D offline fixtures: no network, third-party code or pip downloads."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from lab.exp009d_wheels import (
    PLAN, read_plan, run_project, validate_plan, wheel_digest,
)


class WheelFeasibilityTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(PLAN.read_text(encoding="utf-8"))

    def test_four_projects_twelve_cases_preserved(self):
        self.assertEqual(validate_plan(self.plan), {
            "projects": 4, "cases": 12, "test_outcomes": 0})

    def test_unknown_project_rejected(self):
        with self.assertRaises(ValueError):
            run_project("unknown", python_minor="3.8")

    def test_scoring_must_stay_disabled(self):
        x = copy.deepcopy(self.plan)
        x["scoring"]["enabled"] = True
        with self.assertRaises(ValueError):
            validate_plan(x)

    def test_budgets_must_be_frozen(self):
        x = copy.deepcopy(self.plan)
        x["scoring"]["budgets"] = [1, 6]
        with self.assertRaises(ValueError):
            validate_plan(x)

    def test_seed_must_be_frozen(self):
        x = copy.deepcopy(self.plan)
        x["scoring"]["seed"] = 42
        with self.assertRaises(ValueError):
            validate_plan(x)

    def test_unpinned_requirements_rejected(self):
        x = copy.deepcopy(self.plan)
        x["projects"]["black"]["requirements"].append("request>=1.0")
        with self.assertRaises(ValueError):
            validate_plan(x)

    def test_options_in_requirements_rejected(self):
        x = copy.deepcopy(self.plan)
        x["projects"]["black"]["requirements"] = ["--index-url=https://example.com"]
        with self.assertRaises(ValueError):
            validate_plan(x)

    def test_duplicate_names_rejected(self):
        x = copy.deepcopy(self.plan)
        x["projects"]["black"]["requirements"].append("CLICK==3.0")
        with self.assertRaises(ValueError):
            validate_plan(x)

    def test_not_historic_exact_patch_is_reported(self):
        report = run_project("black", python_minor="3.7")
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["blocker"], "python_minor_mismatch")
        self.assertEqual(len(report["case_ids"]), 3)
        self.assertFalse(report["dependencies_installed"])

    def test_failed_binary_resolution_is_blocker_not_zero_score(self):
        calls = []
        def fake(argv, **kw):
            calls.append((argv, kw))
            return SimpleNamespace(returncode=1)
        report = run_project("black", python_minor="3.8", runner=fake)
        self.assertEqual(report["blocker"], "binary_only_resolution_failed")
        self.assertIsNone(report["policy_scores"])
        self.assertEqual(report["upstream_tests_executed"], 0)
        self.assertEqual(len(calls), 1)
        self.assertIn("--only-binary=:all:", calls[0][0])
        self.assertIn("--no-cache-dir", calls[0][0])
        self.assertNotIn("GITHUB_TOKEN", calls[0][1]["env"])
        self.assertNotIn("PYTHONPATH", calls[0][1]["env"])

    def test_successful_wheel_hash_does_not_install(self):
        def fake(argv, **kw):
            dest = Path(argv[argv.index("--dest") + 1])
            (dest / "click-7.1.1-py2.py3-none-any.whl").write_bytes(b"wheel bytes")
            return SimpleNamespace(returncode=0)
        report = run_project("black", python_minor="3.8", runner=fake)
        self.assertEqual(report["status"], "wheels_downloaded_not_installed")
        self.assertEqual(report["wheel_count"], 1)
        self.assertEqual(len(report["wheels"][0]["sha256"]), 64)
        self.assertFalse(report["environment_reproduction_confirmed"])
        self.assertFalse(report["dependencies_installed"])
        self.assertFalse(report["transitive_wheels_frozen_before_run"])

    def test_unexpected_file_blocks(self):
        def fake(argv, **kw):
            dest = Path(argv[argv.index("--dest") + 1])
            (dest / "malicious.txt").write_text("fake")
            return SimpleNamespace(returncode=0)
        report = run_project("black", python_minor="3.8", runner=fake)
        self.assertEqual(report["blocker"], "no_valid_wheels_or_unexpected_files")

    def test_timeout_is_bounded_blocker(self):
        import subprocess
        def fake(argv, **kw):
            raise subprocess.TimeoutExpired(cmd="SECRET", timeout=1)
        report = run_project("black", python_minor="3.8", runner=fake)
        self.assertEqual(report["blocker"], "download_timeout")
        self.assertNotIn("SECRET", json.dumps(report))

    def test_all_projects_are_predeclared_even_when_blocked(self):
        for name in self.plan["projects"]:
            report = run_project(name, python_minor="0.0")
            self.assertEqual(len(report["case_ids"]), 3)
            self.assertEqual(report["status"], "blocked")
            self.assertIsNone(report["policy_scores"])

    def test_wheel_hash_is_deterministic(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.whl"
            p.write_bytes(b"abc")
            self.assertEqual(wheel_digest(p), __import__("hashlib").sha256(b"abc").hexdigest())


if __name__ == "__main__":
    unittest.main()
