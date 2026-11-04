"""EXP-009B: static, read-only verification of 12 pinned upstream candidates.

No third-party code is imported, installed or executed. This is ONLY source
metadata qualification, never a bug detection or validation experiment.
GitHub token is transmitted exclusively to api.github.com via HTTPS.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
from pathlib import Path
import re
from urllib import error, request

from .exp009b_candidates import MANIFEST, ROOT, validate_manifest

REPOS = {
    "black": "psf/black",
    "fastapi": "fastapi/fastapi",
    "httpie": "httpie/cli",
    "thefuck": "nvbn/thefuck",
}
LICENSE_SIGNATURES = {
    "MIT": ("the mit license", "permission is hereby granted"),
    "BSD-3-Clause": ("redistribution and use in source and binary forms",
                     "neither the name"),
}
MAX_RESPONSE_BYTES = 2_000_000
SHA40 = re.compile(r"[0-9a-f]{40}\Z")


def github_json(repo: str, suffix: str, *, token: str = "") -> dict:
    """Paths are built only by internal code; caller cannot supply a URL."""
    if repo not in REPOS.values() or not suffix.startswith(("/contents/", "/commits/")):
        raise ValueError("Unapproved GitHub API resource")
    url = "https://api.github.com/repos/" + repo + suffix
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "laboratoire-ia-exp009b-static-preflight",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    req = request.Request(url, headers=headers, method="GET")
    with request.urlopen(req, timeout=25) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("Source API response too large")
    parsed = json.loads(raw.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("GitHub resource is not a JSON object")
    return parsed


def content_metadata(source: dict, *, expected_path: str,
                     license_kind: str | None = None) -> dict:
    if (source.get("type") != "file"
            or source.get("path") != expected_path
            or not isinstance(source.get("size"), int)
            or source["size"] < 1
            or not isinstance(source.get("sha"), str)
            or not SHA40.fullmatch(source["sha"])):
        raise ValueError("Pinned GitHub file is missing or malformed")
    result = {"sha": source["sha"], "size": source["size"]}
    if license_kind is not None:
        if license_kind not in LICENSE_SIGNATURES:
            raise ValueError("Unapproved license identifier")
        if source.get("encoding") != "base64":
            raise ValueError("License content encoding missing")
        try:
            body = base64.b64decode(source["content"], validate=False).decode(
                "utf-8", errors="replace").lower()
        except (TypeError, ValueError, binascii.Error, KeyError):
            raise ValueError("License text unreadable") from None
        if not all(s in body for s in LICENSE_SIGNATURES[license_kind]):
            raise ValueError("Historical license does not match declared family")
    return result


def verify_case(case: dict, project: dict, *, token: str = "") -> dict:
    repo = project["repo"]
    ident = case["id"]
    result = {"case": ident, "status": "blocked",
              "checks": {"parent": False, "license_buggy": False,
                         "license_fixed": False, "fixed_test": False},
              "files": {}, "reason": None}
    try:
        fix = github_json(repo, "/commits/" + case["fixed"], token=token)
        parents = fix.get("parents", [])
        if (fix.get("sha") != case["fixed"] or len(parents) != 1
                or parents[0].get("sha") != case["buggy"]):
            raise ValueError("Unexpected historical parent relation")
        result["checks"]["parent"] = True
        for revision, key in (("buggy", "license_buggy"),
                              ("fixed", "license_fixed")):
            source = github_json(
                repo, "/contents/" + project["license_path"]
                + "?ref=" + case[revision], token=token)
            result["files"][key] = content_metadata(
                source, expected_path=project["license_path"],
                license_kind=project["license"])
            result["checks"][key] = True
        source = github_json(
            repo, "/contents/" + case["test_file"] + "?ref=" + case["fixed"],
            token=token)
        if not case["test_file"].endswith(".py"):
            raise ValueError("Only Python test source paths allowed")
        result["files"]["fixed_test"] = content_metadata(
            source, expected_path=case["test_file"])
        result["checks"]["fixed_test"] = True
        result["status"] = "metadata_verified"
    except (error.HTTPError, error.URLError, OSError, ValueError,
            KeyError, TypeError, json.JSONDecodeError):
        # No exception text, URL, traceback, API response or token is persisted.
        result["reason"] = "source_metadata_or_network_check_failed"
    return result


def verify_project(project_name: str, *, token: str = "") -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validate_manifest(manifest)
    if project_name not in REPOS or manifest["projects"][project_name]["repo"] != REPOS[project_name]:
        raise ValueError("Project/repository not allowlisted")
    selected = [c for c in manifest["cases"] if c["project"] == project_name]
    if len(selected) != 3:
        raise ValueError("Expected three registered candidates per project")
    records = [verify_case(c, manifest["projects"][project_name], token=token)
               for c in selected]
    return {
        "experiment": "EXP-009B", "phase": "static_upstream_source_preflight",
        "project": project_name,
        "declared_cases": len(selected), "recorded_cases": len(records),
        "metadata_verified": sum(c["status"] == "metadata_verified"
                                 for c in records),
        "blocked": sum(c["status"] == "blocked" for c in records),
        "records": records,
        "executed_upstream_tests": 0,
        "bug_scores_generated": 0,
        "models_invoked": 0,
        "historical_python_interpreter_qualification": "not_evaluated_here",
        "dependency_compatibility": "not_evaluated_here",
        "claim": "GitHub metadata evidence only; historical tests not run.",
    }


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, choices=sorted(REPOS))
    args = parser.parse_args(argv)
    result = verify_project(args.project, token=os.getenv("GITHUB_TOKEN", ""))
    output = ROOT / "results" / ("exp009b-source-"+args.project+".json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print("EXP009B_SOURCE_PREFLIGHT=" + json.dumps({
        "project": result["project"],
        "checked": result["recorded_cases"],
        "verified": result["metadata_verified"],
        "blocked": result["blocked"],
        "upstream_tests_executed": 0,
        "scores_generated": 0,
    }, sort_keys=True))
    if result["recorded_cases"] != 3 or result["blocked"]:
        raise SystemExit("Candidate source qualification incomplete; inspect artifact")


if __name__ == "__main__":
    main()
