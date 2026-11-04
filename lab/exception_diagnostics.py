"""EXP-009B: bounded, allowlisted exception diagnostics.

Only call on trusted internal fixtures or within isolated read-only CI
worktrees. Never serialize exception values, arguments, locals, messages,
traceback text, stdout, stderr, absolute paths, or external frame paths.
Historical EXP-008B scores and policies remain untouched.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import traceback
import unittest

from .real_bug_priority import RecordingResult, _flatten

MAX_PROJECT_FRAMES = 4
MAX_TESTS = 500
_SAFE_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]{0,79}\Z")
_SAFE_PATH = re.compile(r"[A-Za-z_0-9./-]{1,160}\Z")


def safe_identifier(value: str) -> str:
    return value if _SAFE_IDENTIFIER.fullmatch(value) else "redacted_identifier"


def phase_for_unittest(tb) -> str:
    names = [frame.f_code.co_name for frame, _ in traceback.walk_tb(tb)]
    if any(name in ("tearDown", "tearDownClass", "doCleanups") for name in names):
        return "teardown"
    if any(name in ("setUp", "setUpClass") for name in names):
        return "setup"
    if any(name.startswith("test_") for name in names):
        return "call"
    return "unknown"


def describe_exception(exc: BaseException, tb, root: Path, phase: str) -> dict:
    """Only fixed-schema, strictly project-relative metadata; NO raw traceback."""
    if phase not in ("setup", "call", "teardown", "unknown"):
        raise ValueError("Invalid exception phase")
    project = root.resolve(strict=True)
    frames = []
    for frame, lineno in traceback.walk_tb(tb):
        try:
            relative = Path(frame.f_code.co_filename).resolve().relative_to(project)
        except (ValueError, OSError):
            continue
        filename = relative.as_posix()
        if not _SAFE_PATH.fullmatch(filename) or ".." in relative.parts:
            continue
        frames.append({"file": filename,
                       "function": safe_identifier(frame.f_code.co_name),
                       "line": min(max(int(lineno), 0), 999999)})
    return {
        "exception_type": safe_identifier(type(exc).__name__),
        "phase": phase,
        "project_frames": frames[-MAX_PROJECT_FRAMES:],
    }


class DiagnosticResult(RecordingResult):
    """Unittest-compatible; super may keep local traceback in memory only."""
    def __init__(self, root: Path):
        super().__init__()
        self.root = root
        self.diagnostics = {}

    def addError(self, test, err):
        self.diagnostics[test.id()] = describe_exception(
            err[1], err[2], self.root, phase_for_unittest(err[2]))
        super().addError(test, err)

    def addFailure(self, test, err):
        # Assertion details can matter for fixtures but never persist values.
        self.diagnostics[test.id()] = describe_exception(
            err[1], err[2], self.root, phase_for_unittest(err[2]))
        super().addFailure(test, err)


def capture_suite(suite, root: Path) -> dict:
    tests = list(_flatten(suite))
    ids = [test.id() for test in tests]
    if not ids or len(ids) > MAX_TESTS or len(ids) != len(set(ids)):
        return {"valid": False, "reason": "invalid_collection", "collected": len(ids)}
    recorder = DiagnosticResult(root)
    suite.run(recorder)
    statuses = {key: recorder.status.get(key, "missing") for key in sorted(ids)}
    return {
        "valid": all(value != "missing" for value in statuses.values()),
        "collected": len(ids), "executed": recorder.testsRun,
        "statuses": statuses, "counts": dict(Counter(statuses.values())),
        "exceptions": {k: recorder.diagnostics[k]
                       for k in sorted(recorder.diagnostics)},
    }


def capture_unittest(module: str, root: Path) -> dict:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(module)
    if loader.errors:
        return {"valid": False, "reason": "collection_error",
                "loader_error_count": len(loader.errors)}
    return capture_suite(suite, root)


def capture_pytest(path: str, root: Path) -> dict:
    # Called ONLY by a dedicated isolated CI child process with pytest installed.
    import pytest

    class Plugin:
        def __init__(self):
            self.ids = []
            self.statuses = {}
            self.exceptions = {}

        def pytest_collection_finish(self, session):
            self.ids = [item.nodeid for item in session.items]

        @pytest.hookimpl(hookwrapper=True)
        def pytest_runtest_makereport(self, item, call):
            outcome = yield
            report = outcome.get_result()
            if call.excinfo is not None and report.failed:
                self.exceptions[item.nodeid] = describe_exception(
                    call.excinfo.value, call.excinfo.tb, root, report.when)
                report.lab_is_assertion = (
                    report.when == "call"
                    and isinstance(call.excinfo.value, AssertionError))

        def pytest_runtest_logreport(self, report):
            ident = report.nodeid
            if report.when == "setup":
                if report.failed:
                    self.statuses[ident] = "error"
                elif report.skipped:
                    self.statuses[ident] = "skip"
            elif report.when == "call":
                if report.passed:
                    self.statuses[ident] = "pass"
                elif report.skipped:
                    self.statuses[ident] = "skip"
                elif report.failed:
                    self.statuses[ident] = (
                        "fail" if getattr(report, "lab_is_assertion", False)
                        else "error")
            elif report.when == "teardown" and report.failed:
                self.statuses[ident] = "error"

    plugin = Plugin()
    exit_code = int(pytest.main(
        [path, "-q", "--tb=no", "--disable-warnings",
         "-p", "no:cacheprovider", "-o", "addopts="],
        plugins=[plugin]))
    ids = plugin.ids
    valid = (exit_code in (0, 1) and bool(ids)
             and len(ids) <= MAX_TESTS and len(ids) == len(set(ids))
             and set(ids) == set(plugin.statuses))
    if not valid:
        return {"valid": False, "reason": "pytest_collection_or_execution_error",
                "collected": len(ids), "report_count": len(plugin.statuses),
                "pytest_exit_code": exit_code}
    return {
        "valid": True, "collected": len(ids), "executed": len(ids),
        "statuses": {key: plugin.statuses[key] for key in sorted(ids)},
        "counts": dict(Counter(plugin.statuses.values())),
        "exceptions": {k: plugin.exceptions[k] for k in sorted(plugin.exceptions)},
    }


def redacted_view(report: dict, focus: set[str]) -> dict:
    """Output ONLY explicitly approved test IDs and allowlisted exception data."""
    if not report.get("valid"):
        return {"valid": False, "reason": report.get("reason", "unknown")}
    selected = focus & set(report["statuses"])
    return {
        "valid": True,
        "collected": report["collected"],
        "executed": report["executed"],
        "counts": report["counts"],
        "focus": {key: {
            "status": report["statuses"][key],
            "exception": report["exceptions"].get(key),
        } for key in sorted(selected)},
        "missing_focus_count": len(focus - selected),
    }
