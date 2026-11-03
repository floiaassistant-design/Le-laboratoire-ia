"""EXP-006B: non-executing, license-aware real-bug source preflight.

Checks a fixed manifest and, optionally, publicly accessible upstream
commit parents, MIT license texts and regression test paths. NO installation,
NO third-party code execution, NO agent/LLM calls, and NO policy scoring.
The metadata is recorded as provenance, not copied upstream source code.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "experiments" / "exp006b-manifest.json"
GITHUB_REPO = "cool-RR/PySnooper"
MAX_BYTES = 120_000
SHA = re.compile(r"^[0-9a-f]{40}$")
TEST_PATH = re.compile(r"^tests/[A-Za-z0-9_./-]+[.]py$")
TEST_NAME = re.compile(r"^test_[A-Za-z0-9_]+$")


def validate_manifest(manifest: dict) -> dict:
    """Strict local checks, no network and no inspection of defective code."""
    if not isinstance(manifest, dict) or manifest.get("experiment") != "EXP-006B-METADATA-PREFLIGHT":
        raise ValueError("Invalid experiment declaration")
    dataset = manifest["dataset"]
    alternative = manifest["benchmark_alternative"]
    if dataset["repository"] != "soarsmu/BugsInPy" or alternative["repository"] != "pybughive/pybughive":
        raise ValueError("Unexpected benchmark source")
    for entry in (dataset, alternative):
        if not SHA.fullmatch(entry["commit"]):
            raise ValueError("Unpinned benchmark revision")
        if entry["license_status"] != "not_confirmed_no_root_license":
            raise ValueError("Do not assume benchmark redistribution rights")
    if dataset["redistribution_authorized"] is not False:
        raise ValueError("Do not redistribute unlicensed benchmark dataset")
    study = manifest["study"]
    if study["selected_project"] != GITHUB_REPO or study["project_license"] != "MIT":
        raise ValueError("Unexpected project or license")
    if any(study[field] is not False for field in
           ("source_executed", "benchmark_redistributed", "performance_scored")):
        raise ValueError("Preflight may not assert execution or scoring")
    cases = manifest["cases"]
    if not isinstance(cases, list) or len(cases) != 2:
        raise ValueError("Exactly two predeclared metadata cases")
    ids = set()
    for item in cases:
        if item["id"] not in ("PySnooper-1", "PySnooper-3") or item["id"] in ids:
            raise ValueError("Case ID not unique or not allowed")
        ids.add(item["id"])
        if not SHA.fullmatch(item["buggy"]) or not SHA.fullmatch(item["fixed"]):
            raise ValueError("Buggy/fixed revision not pinned")
        if item["buggy"] == item["fixed"]:
            raise ValueError("Versions must be different")
        path = item["test_path"]
        if (not TEST_PATH.fullmatch(path)
                or ".." in Path(path).parts
                or not TEST_NAME.fullmatch(item["test_name"])):
            raise ValueError("Invalid test selector")
        expected = f"projects/PySnooper/bugs/{item['id'][-1]}/bug.info"
        if item["record_path"] != expected:
            raise ValueError("Unexpected metadata source path")
    if ids != {"PySnooper-1", "PySnooper-3"}:
        raise ValueError("Incomplete cases")
    return manifest


def load_manifest(path: Path = MANIFEST) -> dict:
    return validate_manifest(json.loads(path.read_text(encoding="utf-8")))


def _retrieve(url: str, *, binary: bool = False) -> bytes:
    """Small bounded read; URLs are only derived from validated fixed inputs."""
    request = Request(url, headers={
        "User-Agent": "laboratoire-ia-exp006b-metadata-preflight",
        "Accept": "application/vnd.github+json" if "api.github.com" in url else "text/plain",
    })
    with urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise ValueError(f"Non-OK source status: {response.status}")
        content = response.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError("Unexpectedly large source file")
    return content


def inspect_case(item: dict) -> dict:
    """Verify parent relation, historical MIT file and corrected regression test.

    This does not run the buggy project or claim it reproduces an issue.
    """
    base = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{item['fixed']}"
    commit_api = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{item['fixed']}"
    checks = {}
    try:
        meta = json.loads(_retrieve(commit_api))
        parent_ids = [p["sha"] for p in meta["parents"]]
        checks["fixed_direct_parent_is_buggy"] = parent_ids == [item["buggy"]]
        license_text = _retrieve(f"{base}/LICENSE").decode("utf-8")
        checks["mit_license_in_fixed_revision"] = "MIT License" in license_text
        test_text = _retrieve(f"{base}/{item['test_path']}").decode("utf-8")
        checks["regression_test_in_fixed_revision"] = bool(
            re.search(r"\bdef\s+" + re.escape(item["test_name"]) + r"\s*\(", test_text))
        checks["fixed_sha_matches_api"] = meta.get("sha") == item["fixed"]
    except (HTTPError, URLError, TimeoutError, ValueError, UnicodeError, KeyError, OSError) as exc:
        return {"id": item["id"], "source_verified": False,
                "checks": checks, "network_or_source_error": type(exc).__name__}
    return {"id": item["id"], "source_verified": all(checks.values()),
            "checks": checks,
            "reproduction_tested": False,
            "scoring_eligible": False}


def run(manifest: dict, online: bool) -> dict:
    validate_manifest(manifest)
    results = [inspect_case(case) for case in manifest["cases"]] if online else []
    complete = online and len(results) == len(manifest["cases"]) and all(
        item["source_verified"] for item in results)
    return {
        "experiment": manifest["experiment"],
        "mode": "online_metadata_preflight" if online else "offline_manifest_validation",
        "benchmark_commit": manifest["dataset"]["commit"],
        "source_project": GITHUB_REPO,
        "candidate_count": len(manifest["cases"]),
        "checked_candidates": results,
        "metadata_verified": bool(complete),
        "bugs_executed": 0,
        "bugs_reproduced": 0,
        "scored_cases": 0,
        "candidate_project_count": 1,
        "ready_for_performance_evaluation": False,
        "reason": ("Source metadata alone does not establish reproducibility; "
                   "historical Python, test dependencies and both old/new execution "
                   "must be verified first; benchmark license is still unconfirmed"),
        "limitations": manifest["unresolved"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--online", action="store_true")
    modes.add_argument("--offline", action="store_true")
    parser.add_argument("--output", default="results/exp006b-preflight.json")
    args = parser.parse_args(argv)
    data = run(load_manifest(), online=args.online)
    path = ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print("EXP006B_PREFLIGHT=" + json.dumps({
        "mode": data["mode"],
        "metadata_verified": data["metadata_verified"],
        "candidate_count": data["candidate_count"],
        "checked_candidates": data["checked_candidates"],
        "bugs_executed": data["bugs_executed"],
        "ready_for_performance_evaluation": data["ready_for_performance_evaluation"],
    }, ensure_ascii=False))
    if args.online and not data["metadata_verified"]:
        raise SystemExit("Unverified external benchmark source. Do not report reproducibility.")


if __name__ == "__main__":
    main()
