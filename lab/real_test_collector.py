"""EXP-007B: compare static test identifiers with unittest runtime discovery.

IMPORTANT: unittest discovery IMPORTS test modules and can execute top-level
code and load_tests hooks. Only run on an explicitly trusted checkout.
The collector does NOT execute test methods, buggy versions, or oracles.
It does not compare or optimize bug-detection policies.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

from .real_test_inventory import scan_directory, write_report

MAX_COLLECTED = 10000


def _canonical_test_id(test: unittest.case.TestCase, root: Path) -> str:
    """Reconcile unittest's dotted class.module names with AST path::name."""
    if not isinstance(test, unittest.TestCase):
        raise ValueError("Discovery yielded an unexpected non-TestCase object")
    cls = test.__class__
    module_name = cls.__module__
    method_name = getattr(test, "_testMethodName", None)
    if not isinstance(module_name, str) or not isinstance(method_name, str):
        raise ValueError("Invalid runtime test metadata")
    if not method_name.startswith("test_"):
        raise ValueError("Unexpected runtime method (not test_*)")
    class_name = cls.__qualname__
    if "." in class_name:
        # Nested/dynamically-generated classes need a separate naming policy.
        raise ValueError("Nested/dynamically-generated unittest class not supported")
    # unittest's CLI (discover -s tests) imports 'test_file', while
    # top_level_dir=root imports 'tests.test_file'. Both identify the
    # same checked-out file. Reject ambiguity instead of guessing.
    module_path = Path(*module_name.split(".")).with_suffix(".py")
    candidate_paths = (module_path, Path("tests") / module_path)
    present = [path for path in dict.fromkeys(candidate_paths)
               if (root / path).is_file()]
    if len(present) != 1:
        raise ValueError("Runtime module does not map uniquely to source")
    relative = present[0]
    return relative.as_posix() + "::" + class_name + "::" + method_name


def _flatten_tests(suite: unittest.TestSuite):
    """Yield suite leaves without invoking TestCase.run."""
    if not isinstance(suite, unittest.TestSuite):
        raise ValueError("Unexpected result from unittest discovery")
    for child in suite:
        if isinstance(child, unittest.TestSuite):
            yield from _flatten_tests(child)
        elif isinstance(child, unittest.TestCase):
            yield child
        else:
            raise ValueError("Unknown test object in discovered suite")


def collect_unittest_identifiers(root: Path, scan_dir: str = "tests",
                                 *, allow_imports: bool = False) -> dict:
    """Runtime import collection for trusted LOCAL source only.

    Not a sandbox. It can execute module-level code and unittest load_tests
    hooks. Caller explicitly opts in, including in our own GitHub CI.
    """
    if not allow_imports:
        raise PermissionError("unittest imports test code: --allow-imports required")
    root = Path(root).resolve()
    target = (root / scan_dir).resolve()
    if not target.is_dir():
        raise ValueError("Missing discovery directory")
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError("Discovery directory must remain inside root") from exc
    if (root / scan_dir).is_symlink():
        raise ValueError("Refuse symlink discovery directory")

    # unittest derives module names relative to top_level_dir. Our caller
    # runs from repository root, with root importable, as in GitHub Actions.
    if root != Path.cwd().resolve():
        raise ValueError("Runtime discovery restricted to current trusted checkout")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(target), pattern="test_*.py",
                            top_level_dir=str(root))
    if loader.errors:
        return {"runtime_identifiers": [], "loader_errors": loader.errors,
                "collected_count": 0}
    runtime = []
    for test in _flatten_tests(suite):
        if len(runtime) >= MAX_COLLECTED:
            raise ValueError("Runtime collection exceeded MAX_COLLECTED")
        runtime.append(_canonical_test_id(test, root))
    return {"runtime_identifiers": sorted(runtime), "loader_errors": [],
            "collected_count": len(runtime)}


def compare_identifiers(static_ids: list[str], runtime_ids: list[str]) -> dict:
    """Multiset difference catches missing, spurious, and repeated tests."""
    left, right = Counter(static_ids), Counter(runtime_ids)
    spurious = sorted((left - right).elements())
    missing = sorted((right - left).elements())
    def digest(values: list[str]) -> str:
        return hashlib.sha256(json.dumps(sorted(values), separators=(",", ":"),
                                         ensure_ascii=True).encode("utf-8")).hexdigest()
    return {
        "static_count": len(static_ids),
        "runtime_count": len(runtime_ids),
        "exact_identity_multiset_match": not spurious and not missing,
        "static_only_count": len(spurious),
        "runtime_only_count": len(missing),
        "static_only": spurious,
        "runtime_only": missing,
        "static_duplicates": sorted(n for n, count in left.items() if count > 1),
        "runtime_duplicates": sorted(n for n, count in right.items() if count > 1),
        "static_identity_sha256": digest(static_ids),
        "runtime_identity_sha256": digest(runtime_ids),
    }


def run_comparison(root: Path, *, scan_dir: str = "tests",
                   allow_imports: bool = False) -> dict:
    if not allow_imports:
        raise PermissionError("Runtime discovery imports Python modules")
    root = Path(root).resolve()
    ast_data = scan_directory(root, scan_dir)
    if ast_data["errors"]:
        raise ValueError(f"Invalid static inventory: {ast_data['errors']}")
    if ast_data["candidate_definitions"] < 1:
        raise ValueError("No candidate test definitions")
    runtime = collect_unittest_identifiers(root, scan_dir,
                                           allow_imports=True)
    # A broken import must never be mistaken for an inventory with 0 tests.
    comparison = compare_identifiers(
        [entry["nodeid"] for entry in ast_data["test_candidates"]],
        runtime["runtime_identifiers"])
    return {
        "experiment": "EXP-007B",
        "scope": "first-party unittest identity audit; not third-party validation",
        "scan_dir": scan_dir,
        "file_candidates": ast_data["file_candidates"],
        "parametrized_definitions_not_expanded":
            ast_data["parametrized_definitions_not_expanded"],
        "comparison": comparison,
        "loader_errors": runtime["loader_errors"],
        "module_imports_performed": True,
        "top_level_module_code_may_run": True,
        "unittest_load_tests_hooks_may_run": True,
        "test_methods_run": False,
        "buggy_programs_loaded_for_scoring": False,
        "faults_scored": 0,
        "policies_compared": 0,
        "verified": comparison["exact_identity_multiset_match"]
                    and not runtime["loader_errors"],
        "limitations": [
            "Only first-party trusted unittest suite: imports/load_tests run.",
            "This is NOT a safe collector for untrusted third-party source.",
            "AST candidate list includes pytest-style tests not collected by unittest.",
            "Dynamic, inherited, parametrized or plugin-generated tests may mismatch.",
            "Identity equality does not prove runtime tests pass or detect faults."
        ],
    }


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--scan-dir", default="tests")
    parser.add_argument("--output", default="results/exp007b-identity-report.json")
    parser.add_argument("--allow-imports", action="store_true",
                        help="Explicitly permit module import execution; trusted local code ONLY")
    parser.add_argument("--verify-exact", action="store_true")
    args = parser.parse_args(argv)
    if not args.allow_imports:
        parser.error("Runtime unittest discovery requires --allow-imports")
    root = Path(args.root).resolve()
    report = run_comparison(root, scan_dir=args.scan_dir, allow_imports=True)
    write_report(report, root, args.output)
    c = report["comparison"]
    print("EXP007B_IDENTITIES=" + json.dumps({
        "static_count": c["static_count"],
        "runtime_count": c["runtime_count"],
        "exact_identity_multiset_match": c["exact_identity_multiset_match"],
        "static_only_count": c["static_only_count"],
        "runtime_only_count": c["runtime_only_count"],
        "loader_errors": len(report["loader_errors"]),
        "imports_performed": report["module_imports_performed"],
        "faults_scored": report["faults_scored"],
    }, ensure_ascii=False))
    if args.verify_exact and not report["verified"]:
        raise SystemExit("Identity divergence; see archived JSON")


if __name__ == "__main__":
    main()
