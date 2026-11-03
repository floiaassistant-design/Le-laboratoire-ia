"""EXP-007A: static, non-executing inventory of potential Python test cases.

Reads only syntax from test_*.py / *_test.py. No imports, pytest collection,
subprocesses, result/oracle lookup, ranking, or third-party dependencies.
Candidates are definitions, not proof that a framework can collect/run them.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = frozenset({
    ".git", ".hg", ".svn", ".venv", "venv", "env", "site-packages",
    "__pycache__", "build", "dist", ".tox", ".nox", ".pytest_cache",
    "node_modules", "third_party",
})
MAX_FILES = 1000
MAX_SOURCE_BYTES = 512_000


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return base + "." + node.attr if base else node.attr
    if isinstance(node, ast.Call):
        return _dotted(node.func)
    return ""


def _bucket(value: int) -> str:
    if value == 0:
        return "0"
    if value == 1:
        return "1"
    if value <= 3:
        return "2-3"
    if value <= 7:
        return "4-7"
    return "8+"


def _summarize_test(node: ast.FunctionDef | ast.AsyncFunctionDef,
                    path: str, owner: str | None, kind: str) -> dict[str, Any]:
    descendants = tuple(ast.walk(node))
    counts = {
        "asserts": sum(isinstance(n, ast.Assert) for n in descendants),
        "calls": sum(isinstance(n, ast.Call) for n in descendants),
        "branches": sum(isinstance(n, (ast.If, ast.IfExp, ast.Match))
                        for n in descendants),
        "loops": sum(isinstance(n, (ast.For, ast.AsyncFor, ast.While))
                     for n in descendants),
        "raises": sum(isinstance(n, ast.Raise) for n in descendants),
        "context_managers": sum(isinstance(n, (ast.With, ast.AsyncWith))
                                for n in descendants),
        "try_blocks": sum(isinstance(n, ast.Try) for n in descendants),
    }
    decorator_names = [_dotted(d) for d in node.decorator_list]
    is_parametrized = any(d.endswith(".parametrize") or d == "parametrize"
                          for d in decorator_names)
    has_fixture = any(d.endswith(".fixture") or d == "fixture"
                      for d in decorator_names)
    parameters = len(node.args.posonlyargs) + len(node.args.args) + len(node.args.kwonlyargs)
    markers = {
        "kind:" + kind,
        "async:" + str(isinstance(node, ast.AsyncFunctionDef)).lower(),
        "parametrized:" + str(is_parametrized).lower(),
        "fixture_decorator:" + str(has_fixture).lower(),
        "parameters:" + _bucket(parameters),
    }
    markers.update(name + ":" + _bucket(value) for name, value in counts.items())
    nodeid = path + "::" + (owner + "::" if owner else "") + node.name
    return {
        "nodeid": nodeid,
        "file": path,
        "class": owner,
        "function": node.name,
        "kind": kind,
        "lineno": node.lineno,
        "end_lineno": node.end_lineno,
        "is_async": isinstance(node, ast.AsyncFunctionDef),
        "parametrized_definition": is_parametrized,
        "parameters": parameters,
        "structure_counts": counts,
        "static_features": sorted(markers),
    }


def inventory_source(source: str, relative_path: str) -> list[dict[str, Any]]:
    """Parse only top-level test functions and direct methods on test classes.

    Literal test values, pass/fail outcomes, expected outputs and fixed/buggy
    code are not inspected. Nested functions are never counted as tests.
    """
    tree = ast.parse(source, filename=relative_path)
    results: list[dict[str, Any]] = []
    for stmt in tree.body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if stmt.name.startswith("test_"):
                results.append(_summarize_test(stmt, relative_path, None,
                                               "pytest_function"))
        elif isinstance(stmt, ast.ClassDef):
            unittest_subclass = any(_dotted(base).split(".")[-1] == "TestCase"
                                    for base in stmt.bases)
            pytest_class = stmt.name.startswith("Test")
            if not (unittest_subclass or pytest_class):
                continue
            kind = "unittest_method" if unittest_subclass else "pytest_method"
            for method in stmt.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if method.name.startswith("test_"):
                        results.append(_summarize_test(method, relative_path,
                                                       stmt.name, kind))
    return results


def _inside(root: Path, child: Path) -> bool:
    try:
        child.relative_to(root)
        return True
    except ValueError:
        return False


def scan_directory(root: Path, scan_dir: str = "tests") -> dict[str, Any]:
    """Never follows symlink directories/files, never executes inspected code."""
    root = Path(root).resolve()
    target = root / scan_dir
    resolved = target.resolve()
    if not _inside(root, resolved) or target.is_symlink():
        raise ValueError("Scan path must remain inside the root and not be a symlink")
    if not resolved.is_dir():
        raise ValueError("Scan directory does not exist")
    data: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    files_seen = 0
    parsed = 0
    for base, subdirs, filenames in os.walk(resolved, followlinks=False):
        folder = Path(base)
        subdirs[:] = sorted(d for d in subdirs if d not in SKIP_DIRS
                            and not (folder / d).is_symlink())
        for name in sorted(filenames):
            if not name.endswith(".py") or not (
                    name.startswith("test_") or name.endswith("_test.py")):
                continue
            path = folder / name
            if path.is_symlink():
                continue
            files_seen += 1
            if files_seen > MAX_FILES:
                raise ValueError("Test-file scan exceeded fixed MAX_FILES")
            relative = path.relative_to(root).as_posix()
            try:
                if path.stat().st_size > MAX_SOURCE_BYTES:
                    errors.append({"file": relative, "reason": "too_large"})
                    continue
                file_source = path.read_text(encoding="utf-8-sig")
                entries = inventory_source(file_source, relative)
            except SyntaxError as exc:
                errors.append({"file": relative, "reason": "syntax_error",
                               "line": str(exc.lineno)})
                continue
            except (UnicodeError, OSError, ValueError):
                errors.append({"file": relative, "reason": "unreadable_source"})
                continue
            parsed += 1
            data.extend(entries)
    data.sort(key=lambda item: (item["file"], item["lineno"], item["nodeid"]))
    seen: set[str] = set()
    for item in data:
        if item["nodeid"] in seen:
            errors.append({"file": item["file"], "reason": "duplicate_definition",
                           "nodeid": item["nodeid"]})
        seen.add(item["nodeid"])
    return {
        "experiment": "EXP-007A",
        "status": "static_inventory_only_not_executable_collection",
        "scan_dir": resolved.relative_to(root).as_posix(),
        "file_candidates": files_seen,
        "files_parsed": parsed,
        "candidate_definitions": len(data),
        "parametrized_definitions_not_expanded":
            sum(bool(x["parametrized_definition"]) for x in data),
        "errors": errors,
        "test_candidates": data,
        "code_executed": False,
        "buggy_programs_read": False,
        "oracles_consulted": False,
        "tests_executed": False,
        "bugs_scored": 0,
        "strategies_ranked": False,
        "notes": [
            "AST definitions are candidates, not necessarily runnable tests.",
            "Dynamic pytest collection, plugins, fixtures, skips and inheritance are not resolved.",
            "Parametrized definitions represent multiple runtime cases but are not expanded.",
            "No file or function was imported or executed during inventory."
        ],
    }


def write_report(report: dict, root: Path, output: str) -> Path:
    root = Path(root).resolve()
    path = (root / output).resolve()
    if not _inside(root, path) or path == root:
        raise ValueError("Report output must stay inside root")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--scan-dir", default="tests")
    parser.add_argument("--output", default="results/exp007a-inventory.json")
    parser.add_argument("--require-tests", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root)
    report = scan_directory(root, args.scan_dir)
    write_report(report, root, args.output)
    print("EXP007A_INVENTORY=" + json.dumps({
        "file_candidates": report["file_candidates"],
        "files_parsed": report["files_parsed"],
        "candidate_definitions": report["candidate_definitions"],
        "parametrized_definitions_not_expanded":
            report["parametrized_definitions_not_expanded"],
        "error_count": len(report["errors"]),
        "bugs_scored": report["bugs_scored"],
        "code_executed": report["code_executed"],
    }, ensure_ascii=False))
    if report["errors"] or (args.require_tests and not report["candidate_definitions"]):
        raise SystemExit("Invalid or empty static inventory; see archived JSON")


if __name__ == "__main__":
    main()
