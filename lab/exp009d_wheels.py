"""EXP-009D: preregistered binary-wheel FEASIBILITY probe, not a test run.

No upstream imports, source code execution, installations, test outcomes,
models or policy scoring. Only download wheels from public PyPI in CI.
A missing/unsatisfiable wheel is an explicit BLOCKER, not a negative score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic

from .exp009b_candidates import MANIFEST as CANDIDATES, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "experiments" / "exp009d-wheel-feasibility.json"
PROJECTS = ("black", "fastapi", "httpie", "thefuck")
REQ = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,60}==[0-9][A-Za-z0-9_.+!-]{0,50}\Z")
FILENAME = re.compile(r"[A-Za-z0-9_.+-]{1,180}\.whl\Z")
TIMEOUT_SECONDS = 165


def read_plan():
    data = json.loads(PLAN.read_text(encoding="utf-8"))
    validate_plan(data)
    return data


def validate_plan(data):
    if (data.get("experiment") != "EXP-009D" or
        data.get("phase") != "dependency_wheel_feasibility_before_any_new_case_test" or
        data.get("status") != "exploratory_environment_probe_not_full_lock_or_scoring" or
        data.get("source_manifest") != "experiments/exp009b-candidates.json" or
        data.get("index") != "https://pypi.org/simple" or
        data.get("tested_case_count") != 0):
        raise ValueError("Unfrozen or scored environment probe")
    candidates = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    validate_manifest(candidates)
    if set(data.get("projects", {})) != set(PROJECTS):
        raise ValueError("Expected four distinct projects")
    for project, spec in data["projects"].items():
        if (spec.get("python") not in ("3.7", "3.8") or
            spec.get("historical_python") != candidates["projects"][project]["python"]):
            raise ValueError("Historical Python mismatch")
        deps = spec.get("requirements")
        if (not isinstance(deps, list) or not (1 <= len(deps) <= 20) or
            any(not isinstance(x, str) or not REQ.fullmatch(x) for x in deps)):
            raise ValueError("Only short, exact, wheel-only requirement strings allowed")
        names = [s.split("==")[0].lower().replace("_", "-") for s in deps]
        if len(set(names)) != len(names):
            raise ValueError("Duplicate dependency")
        if len([c for c in candidates["cases"] if c["project"] == project]) != 3:
            raise ValueError("Inconsistent case cohort")
    scoring = data.get("scoring", {})
    if (scoring.get("enabled") is not False or
        scoring.get("policies") != ["lexical", "seeded_random", "structural_diversity"] or
        scoring.get("seed") != 20261103 or
        scoring.get("budgets") != [1, 3, 6, 12] or
        scoring.get("code_under_test_executed") is not False or
        data.get("transitive_dependencies_pinned_before_resolution") is not False):
        raise ValueError("Frozen baselines and honest environment scope required")
    return {"projects": 4, "cases": 12, "test_outcomes": 0}


def wheel_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_project(name, *, python_minor=None, runner=None):
    data = read_plan()
    if name not in PROJECTS:
        raise ValueError("Unknown project")
    spec = data["projects"][name]
    actual = ".".join(str(x) for x in sys.version_info[:2]) if python_minor is None else python_minor
    cases = json.loads(CANDIDATES.read_text(encoding="utf-8"))["cases"]
    ids = [c["id"] for c in cases if c["project"] == name]
    # One project-level wheel set is shared by three bug candidates; never
    # pretend three independent environment observations have been made.
    result = {
        "experiment": "EXP-009D", "project": name, "case_ids": ids,
        "requested_python_minor": spec["python"],
        "actual_python_minor": actual,
        "historical_python_patch": spec["historical_python"],
        "status": "blocked",
        "blocker": None, "direct_requirements": list(spec["requirements"]),
        "wheels": [], "wheel_count": 0, "total_wheel_bytes": 0,
        "transitive_wheels_frozen_before_run": False,
        "dependencies_installed": False, "upstream_imported": False,
        "upstream_tests_executed": 0, "policy_scores": None,
        "environment_reproduction_confirmed": False,
        "source_manifest": "experiments/exp009b-candidates.json",
        "probe_manifest": "experiments/exp009d-wheel-feasibility.json",
    }
    if actual != spec["python"]:
        result["blocker"] = "python_minor_mismatch"
        return result
    with TemporaryDirectory(prefix="exp009d-wheels-") as folder:
        dest = Path(folder)
        env = {k: v for k, v in os.environ.items()
               if not k.upper().startswith(("PIP_", "PYTHONPATH", "PYTHONHOME"))}
        env.update({
            "PIP_CONFIG_FILE": os.devnull, "PIP_NO_INPUT": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PYTHONNOUSERSITE": "1",
            "PIP_CACHE_DIR": str(dest / "cache"),
        })
        argv = [
            sys.executable, "-s", "-m", "pip", "download",
            "--only-binary=:all:", "--disable-pip-version-check",
            "--no-input", "--no-cache-dir",
            "--index-url", data["index"], "--dest", str(dest),
            "--timeout", "15", "--retries", "1",
        ] + spec["requirements"]
        started = monotonic()
        try:
            execute = runner or subprocess.run
            proc = execute(argv, env=env, timeout=TIMEOUT_SECONDS,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, check=False)
            result["wall_seconds"] = round(monotonic() - started, 3)
            if proc.returncode != 0:
                result["blocker"] = "binary_only_resolution_failed"
                return result
            files = sorted(x for x in dest.iterdir() if x.is_file())
            if (not files or len(files) > 100 or
                any(not FILENAME.fullmatch(x.name) for x in files)):
                result["blocker"] = "no_valid_wheels_or_unexpected_files"
                return result
            result["wheels"] = [
                {"filename": x.name, "sha256": wheel_digest(x),
                 "bytes": x.stat().st_size} for x in files
            ]
            result["wheel_count"] = len(files)
            result["total_wheel_bytes"] = sum(w["bytes"] for w in result["wheels"])
            result["status"] = "wheels_downloaded_not_installed"
        except subprocess.TimeoutExpired:
            result["blocker"] = "download_timeout"
        except (OSError, ValueError):
            result["blocker"] = "local_download_or_hash_error"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, choices=PROJECTS)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    if args.offline:
        print("EXP009D_PLAN=" + json.dumps(validate_plan(read_plan())))
        return
    report = run_project(args.project)
    target = ROOT / "results" / ("exp009d-wheels-" + args.project + ".json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=True,
                                 sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    print("EXP009D_WHEEL_PROBE=" + json.dumps({
        "project": args.project, "status": report["status"],
        "blocker": report["blocker"], "wheels": report["wheel_count"],
        "candidate_ids": report["case_ids"],
        "upstream_tests": 0, "scores": 0,
    }, sort_keys=True))
    # Blocked environment is a published result, not a CI failure; the job
    # fails only when it cannot produce a valid report for every declared ID.
    if len(report["case_ids"]) != 3:
        raise SystemExit("Incomplete candidate denominator")


if __name__ == "__main__":
    main()
