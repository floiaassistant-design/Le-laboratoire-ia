"""EXP-009E: static AST inventory of fixed-commit historical test files.

NO upstream execution, NO imports from third-party repos, NO test outcomes.
A syntax-derived test definition is NOT a validated runtime test ID.
"""
from __future__ import annotations

import argparse
import ast
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import re

from .exp009b_candidates import MANIFEST as CANDIDATES, ROOT, validate_manifest
from .exp009b_source_preflight import github_json, content_metadata

HYPOTHESES = ROOT / "experiments" / "exp009e-semantic-hypotheses.json"
MAX_TEST_SOURCE = 1_000_000
MAX_STATIC_DEFINITIONS = 1000
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]{0,100}\Z")
PROJECTS = ("black", "fastapi", "httpie", "thefuck")


def validate_semantics(hypotheses, candidates):
    if (hypotheses.get("experiment") != "EXP-009E"
            or hypotheses.get("phase")
               != "preexecution_semantic_hypotheses_and_static_testbank"
            or hypotheses.get("candidate_source")
               != "experiments/exp009b-candidates.json"
            or hypotheses.get("status")
               != "hypotheses_only_not_primary_or_secondary_scoring"
            or hypotheses.get("cohort_size") != 12
            or hypotheses.get("projects") != list(PROJECTS)
            or hypotheses.get("secondary_oracle_global_enabled") is not False
            or hypotheses.get("policies_frozen") !=
               ["lexical", "seeded_random", "structural_diversity"]
            or hypotheses.get("seed") != 20261103
            or hypotheses.get("budgets") != [1, 3, 6, 12]
            or hypotheses.get("third_party_tests_executed") != 0
            or hypotheses.get("bug_detection_scores_generated") != 0):
        raise ValueError("Semantic hypothesis plan is not frozen")
    source = hypotheses.get("upstream_patch_source", {})
    if (source.get("repo") != "soarsmu/BugsInPy"
            or source.get("sha") !=
               "11c5f1eea954a42132cfd06bf257766a7963e0fd"):
        raise ValueError("Unknown upstream patch provenance")
    declared = hypotheses.get("cases", [])
    ids = [c["id"] for c in candidates["cases"]]
    if not isinstance(declared, list) or [c.get("id") for c in declared] != ids:
        raise ValueError("All 12 candidate identities and order must match")
    for c in declared:
        if (not isinstance(c.get("behavioral_hypothesis_from_known_fix"), str)
                or len(c["behavioral_hypothesis_from_known_fix"]) < 15
                or not c.get("environment_requirements")
                or c.get("witness_inputs_defined") is not False
                or c.get("expected_outputs_defined") is not False
                or c.get("exact_runtime_test_ids_frozen") is not False
                or c.get("secondary_oracle_enabled") is not False
                or c.get("bug_outcomes_observed") is not False):
            raise ValueError("Do not turn patch-informed hypotheses into scored oracles")
    return {"cases": len(ids), "scores": 0, "executed": 0}


def _mark_parametrization(node):
    for deco in node.decorator_list:
        attr = deco.func if isinstance(deco, ast.Call) else deco
        if (isinstance(attr, ast.Attribute)
                and attr.attr in ("parametrize", "parameterized", "expand")):
            return True
        if isinstance(attr, ast.Name) and attr.id in ("parametrize", "parameterized"):
            return True
    return False


def collect_definitions(code):
    tree = ast.parse(code)
    definitions = []
    parametrized = []
    rejected = 0
    for obj in tree.body:
        if isinstance(obj, (ast.FunctionDef, ast.AsyncFunctionDef)) and obj.name.startswith("test_"):
            candidates = [("", obj)]
        elif isinstance(obj, ast.ClassDef):
            candidates = [
                (obj.name, method) for method in obj.body
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                and method.name.startswith("test_")
            ]
        else:
            continue
        for owner, node in candidates:
            name = owner + "." + node.name if owner else node.name
            if (not IDENTIFIER.fullmatch(owner) and owner
                    or not IDENTIFIER.fullmatch(node.name)):
                rejected += 1
                continue
            definitions.append(name)
            if _mark_parametrization(node):
                parametrized.append(name)
    definitions.sort()
    parametrized.sort()
    if not definitions or len(definitions) > MAX_STATIC_DEFINITIONS:
        raise ValueError("No usable test definitions or oversized test bank")
    if len(definitions) != len(set(definitions)):
        raise ValueError("Duplicate lexical test definition")
    digest = hashlib.sha256(
        json.dumps(definitions, separators=(",", ":"),
                   ensure_ascii=True).encode("utf-8")).hexdigest()
    return {
        "definition_count": len(definitions),
        "static_definitions": definitions,
        "parametrized_definitions": parametrized,
        "parametrized_count": len(parametrized),
        "unsafe_identifier_count": rejected,
        "definition_ids_are_runtime_test_ids": False,
        "static_id_list_sha256": digest,
        "dynamic_collection_not_verified": True,
    }


def inspect_case(case, project, *, token=""):
    record = {
        "case": case["id"], "project": case["project"],
        "status": "blocked", "reason": None,
        "revision": case["fixed"], "test_file": case["test_file"],
        "file_blob_sha": None, "summary": None,
    }
    try:
        upstream = github_json(
            project["repo"], "/contents/" + case["test_file"]
            + "?ref=" + case["fixed"], token=token)
        meta = content_metadata(
            upstream, expected_path=case["test_file"])
        if (upstream.get("encoding") != "base64"
                or meta["size"] > MAX_TEST_SOURCE):
            raise ValueError("Test source not safely readable")
        code = base64.b64decode(upstream["content"]).decode("utf-8-sig")
        record["file_blob_sha"] = meta["sha"]
        record["summary"] = collect_definitions(code)
        record["status"] = "static_ast_inventory_only"
    except (ValueError, OSError, TypeError, KeyError,
            SyntaxError, UnicodeError, binascii.Error):
        record["reason"] = "upstream_file_or_static_ast_error"
    return record


def inspect_project(project, *, token=""):
    manifest = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    validate_manifest(manifest)
    hypotheses = json.loads(HYPOTHESES.read_text(encoding="utf-8"))
    validate_semantics(hypotheses, manifest)
    if project not in PROJECTS:
        raise ValueError("Unregistered source project")
    cases = [c for c in manifest["cases"] if c["project"] == project]
    if len(cases) != 3:
        raise ValueError("Incomplete fixed cohort")
    entries = [inspect_case(c, manifest["projects"][project], token=token)
               for c in cases]
    return {
        "experiment": "EXP-009E", "project": project,
        "phase": "static_test_bank_not_executed",
        "declared_cases": 3, "inspected_cases": len(entries),
        "static_success": sum(x["status"] == "static_ast_inventory_only"
                              for x in entries),
        "blocked": sum(x["status"] == "blocked" for x in entries),
        "cases": entries,
        "upstream_test_methods_executed": 0,
        "runtime_test_ids_established": False,
        "secondary_oracle_enabled": False,
        "bug_scores_generated": 0,
        "warning": "AST definitions may differ from unittest/pytest runtime IDs."
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", choices=PROJECTS, required=True)
    args = parser.parse_args(argv)
    r = inspect_project(args.project, token=os.getenv("GITHUB_TOKEN", ""))
    output = ROOT / "results" / ("exp009e-testbank-" + args.project + ".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(r, indent=2, ensure_ascii=True,
                                 sort_keys=True) + "\n", encoding="utf-8")
    print("EXP009E_STATIC_TESTBANK=" + json.dumps({
        "project": args.project, "inspected": r["inspected_cases"],
        "success": r["static_success"], "blocked": r["blocked"],
        "static_definitions": sum(
            x["summary"]["definition_count"]
            for x in r["cases"] if x["summary"]),
        "runtime_ids": False, "upstream_tests_executed": 0,
        "bug_scores": 0,
    }, sort_keys=True))
    if r["inspected_cases"] != 3:
        raise SystemExit("Expected all predeclared candidates")


if __name__ == "__main__":
    main()
