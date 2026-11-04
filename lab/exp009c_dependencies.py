"""EXP-009C: static dependency-descriptor inventory for 12 historical candidates.

Read pinned public text only; NEVER import, execute, install or evaluate
upstream setup.py/requirements. No tests, policies, oracle or scores here.
"""
from __future__ import annotations

import argparse
import ast
import base64
import binascii
import json
import os
from pathlib import Path
import re
import tomllib

from .exp009b_candidates import MANIFEST, ROOT, validate_manifest
from .exp009b_source_preflight import github_json, content_metadata

DESCRIPTORS = {
    "black": ("Pipfile.lock", "setup.py"),
    "fastapi": ("pyproject.toml",),
    "httpie": ("requirements-dev.txt", "setup.py"),
    "thefuck": ("requirements.txt", "setup.py"),
}
MAX_SOURCE_BYTES = 500_000


def unpack_source(source: dict, path: str) -> tuple[dict, str]:
    meta = content_metadata(source, expected_path=path)
    if meta["size"] > MAX_SOURCE_BYTES or source.get("encoding") != "base64":
        raise ValueError("Dependency source too large or not base64")
    try:
        content = base64.b64decode(source["content"]).decode("utf-8")
    except (KeyError, TypeError, UnicodeError, ValueError, binascii.Error):
        raise ValueError("Dependency source not readable") from None
    return meta, content


def dependency_summary(names: list[str]) -> dict:
    if not all(isinstance(x, str) for x in names):
        raise ValueError("Invalid dependency entry")
    lines = [x.strip() for x in names if x.strip() and not x.lstrip().startswith("#")]
    return {
        "declared": len(lines),
        "exact_equality_constraints": sum(bool(re.search(r"(?<![=!<>])==(?!=)", x))
                                          for x in lines),
        "non_exact_or_unbounded_constraints": sum(
            not bool(re.search(r"(?<![=!<>])==(?!=)", x)) for x in lines),
    }


def static_setup_summary(text: str) -> dict:
    """AST-only; literal dependency lists are a lower bound, NOT resolved env."""
    tree = ast.parse(text)
    assigned = {}
    dynamic = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = (node.targets if isinstance(node, ast.Assign)
                       else [node.target])
            for target in targets:
                if isinstance(target, ast.Name) and target.id in (
                    "install_requires", "tests_require"):
                    try:
                        value = ast.literal_eval(node.value)
                        if isinstance(value, list):
                            assigned[target.id] = value
                    except (ValueError, TypeError, SyntaxError):
                        dynamic = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            base = node.func.value
            if (isinstance(base, ast.Name)
                    and base.id in ("install_requires", "tests_require")
                    and node.func.attr in ("append", "extend", "insert")):
                dynamic = True
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "setup":
            for keyword in node.keywords:
                if keyword.arg in ("install_requires", "tests_require"):
                    if isinstance(keyword.value, ast.Name):
                        if keyword.value.id not in assigned:
                            dynamic = True
                    else:
                        try:
                            value = ast.literal_eval(keyword.value)
                            if isinstance(value, list):
                                assigned[keyword.arg] = value
                            else:
                                dynamic = True
                        except (ValueError, TypeError, SyntaxError):
                            dynamic = True
    a = dependency_summary(assigned.get("install_requires", []))
    b = dependency_summary(assigned.get("tests_require", []))
    return {"format": "setup_py_static_ast",
            "runtime_literal": a, "test_literal": b,
            "dynamic_requirements_present": dynamic,
            "source_was_executed": False}


def static_profile(path: str, text: str) -> dict:
    if path == "Pipfile.lock":
        data = json.loads(text)
        pinned, loose, local = 0, 0, 0
        for section in ("default", "develop"):
            deps = data.get(section, {})
            if not isinstance(deps, dict):
                raise ValueError("Invalid Pipfile lock section")
            for attrs in deps.values():
                if not isinstance(attrs, dict):
                    raise ValueError("Invalid lock dependency")
                if "path" in attrs or "git" in attrs or "editable" in attrs:
                    local += 1
                elif isinstance(attrs.get("version"), str) and attrs["version"].startswith("=="):
                    pinned += 1
                else:
                    loose += 1
        return {"format": "pipfile_lock_static",
                "exact_locked_entries": pinned,
                "unbounded_or_unclassified_entries": loose,
                "local_or_editable_entries": local,
                "installability_verified": False}
    if path == "pyproject.toml":
        data = tomllib.loads(text)
        flit = data.get("tool", {}).get("flit", {}).get("metadata", {})
        if not isinstance(flit, dict):
            raise ValueError("Unsupported historical pyproject metadata")
        core = flit.get("requires", [])
        extras = flit.get("requires-extra", {})
        if not isinstance(core, list) or not isinstance(extras, dict):
            raise ValueError("Invalid flit requirements")
        extra_entries = [entry for group in extras.values() for entry in group]
        return {"format": "flit_pyproject_static",
                "core": dependency_summary(core),
                "optional": dependency_summary(extra_entries),
                "python_requirement_declared": isinstance(flit.get("requires-python"), str),
                "installability_verified": False}
    if path in ("requirements.txt", "requirements-dev.txt"):
        lines = text.splitlines()
        if any(l.lstrip().startswith(("-r ", "-e ", "--", "git+"))
               for l in lines):
            return {"format": "requirements_static",
                    "has_external_or_dynamic_includes": True,
                    "declarations": dependency_summary(lines),
                    "installability_verified": False}
        return {"format": "requirements_static",
                "has_external_or_dynamic_includes": False,
                "declarations": dependency_summary(lines),
                "installability_verified": False}
    if path == "setup.py":
        return static_setup_summary(text)
    raise ValueError("Unapproved dependency descriptor")


def inspect_case(case: dict, project: dict, *, token: str = "") -> dict:
    result = {"case": case["id"], "status": "blocked",
              "dependencies": [], "reason": None}
    for path in DESCRIPTORS[case["project"]]:
        try:
            source = github_json(
                project["repo"], "/contents/" + path + "?ref=" + case["fixed"],
                token=token)
            meta, contents = unpack_source(source, path)
            profile = static_profile(path, contents)
            result["dependencies"].append(
                {"path": path, "blob_sha": meta["sha"],
                 "size": meta["size"], "observations": profile})
        except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError,
                SyntaxError, binascii.Error):
            # No raw upstream code/traceback/error text included in report.
            result["reason"] = "dependency_metadata_unavailable_or_unreadable"
            return result
    result["status"] = "static_metadata_inspected"
    return result


def inspect_project(name: str, *, token: str = "") -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validate_manifest(manifest)
    if name not in DESCRIPTORS:
        raise ValueError("Unknown upstream project")
    selected = [case for case in manifest["cases"] if case["project"] == name]
    if len(selected) != 3:
        raise ValueError("Missing candidate")
    records = [inspect_case(case, manifest["projects"][name], token=token)
               for case in selected]
    return {
        "experiment": "EXP-009C",
        "phase": "static_dependency_metadata_preflight",
        "project": name, "cases_declared": 3,
        "cases_inspected": len(records),
        "source_profiles_complete": sum(
            c["status"] == "static_metadata_inspected" for c in records),
        "blocked": sum(c["status"] == "blocked" for c in records),
        "cases": records,
        "source_code_executed": False,
        "dependency_environment_installed": False,
        "historical_compatibility_proven": False,
        "candidate_detection_scores": None,
        "models_evaluated": 0,
    }


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", choices=sorted(DESCRIPTORS), required=True)
    args = parser.parse_args(argv)
    report = inspect_project(args.project, token=os.getenv("GITHUB_TOKEN", ""))
    output = ROOT / "results" / ("exp009c-deps-" + args.project + ".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print("EXP009C_DEPENDENCIES=" + json.dumps({
        "project": args.project,
        "declared": report["cases_declared"],
        "inspected": report["source_profiles_complete"],
        "blocked": report["blocked"],
        "upstream_imports": 0,
        "bug_scores": 0,
    }, sort_keys=True))
    if report["cases_inspected"] != 3 or report["blocked"]:
        raise SystemExit("Incomplete dependency metadata; inspect artifact")


if __name__ == "__main__":
    main()
