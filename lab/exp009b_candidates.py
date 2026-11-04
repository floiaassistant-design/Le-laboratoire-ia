"""Offline structural checks for EXP-009B prospective candidate manifest.
This script imports no upstream code and makes no network requests.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "experiments/exp009b-candidates.json"
BANNED = frozenset(("youtube-dl", "tornado", "cookiecutter",
                    "PySnooper", "tqdm", "QuixBugs"))
ALLOWED = frozenset(("black", "fastapi", "httpie", "thefuck"))


def validate_manifest(data: dict) -> dict:
    if (data.get("experiment") != "EXP-009B"
            or data.get("phase") != "new_cohort_metadata_preflight"
            or data.get("status") != "preliminary_candidates_not_frozen_or_executed"):
        raise ValueError("Only preliminary, non-scored candidate metadata permitted")
    src = data.get("source", {})
    if (src.get("repo") != "soarsmu/BugsInPy"
            or src.get("sha") != "11c5f1eea954a42132cfd06bf257766a7963e0fd"
            or src.get("redistribute_source_code") is not False):
        raise ValueError("Source/provenance changed")
    ps = data.get("projects", {})
    if set(ps) != ALLOWED or set(ps) & BANNED:
        raise ValueError("Wrong source projects")
    for name, meta in ps.items():
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", meta.get("repo", "")):
            raise ValueError("Invalid GitHub repo name")
        if meta.get("license") not in ("MIT", "BSD-3-Clause"):
            raise ValueError("Unverified licence")
        if meta.get("license_each_revision_pending") is not True:
            raise ValueError("Do not overstate licence coverage")
        if meta.get("license_first_fixed_revision_inspected") is not True:
            raise ValueError("Licence family not sampled")
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != 12:
        raise ValueError("Exactly twelve metadata candidates expected")
    ids = []
    for case in cases:
        p = case.get("project")
        if p not in ALLOWED:
            raise ValueError("Previously used or unknown project")
        if not re.fullmatch(p + r"-[1-9][0-9]*", case.get("id", "")):
            raise ValueError("Unexpected case id")
        ids.append(case["id"])
        for field in ("fixed", "buggy"):
            if not re.fullmatch(r"[0-9a-f]{40}", case.get(field, "")):
                raise ValueError("Unpinned historical revision")
        if case["fixed"] == case["buggy"] or case.get("commit_parent_verified") is not True:
            raise ValueError("Parent verification incomplete")
        test_file = case.get("test_file", "")
        if (not re.fullmatch(r"[A-Za-z0-9_./-]+\.py", test_file)
                or ".." in Path(test_file).parts):
            raise ValueError("Unsafe or missing test-file metadata")
        if not re.fullmatch(r"3\.[0-9]+\.[0-9]+", case.get("declared_python", "")):
            raise ValueError("Historical Python version required")
        if (case.get("case_status") != "metadata_only"
                or case.get("test_suite_execution") != "not_executed"
                or case.get("oracle_status") != "not_predefined"):
            raise ValueError("No experimental evidence exists yet")
        if any(key in case for key in ("score", "result", "detection", "outcome")):
            raise ValueError("No scored result allowed in metadata")
    if len(set(ids)) != len(ids) or Counter(x["project"] for x in cases) != dict.fromkeys(
            sorted(ALLOWED), 3):
        raise ValueError("Expected three unique cases in each of four projects")
    if not BANNED <= set(data.get("prior_project_exclusion", [])):
        raise ValueError("Past projects must stay excluded")
    return {"experiment": "EXP-009B", "status": "metadata_only",
            "project_count": len(ps), "candidate_count": len(ids),
            "tests_executed": 0, "scores_generated": 0}


def main():
    report = validate_manifest(json.loads(MANIFEST.read_text(encoding="utf-8")))
    print("EXP009B_CANDIDATE_PREFLIGHT=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
