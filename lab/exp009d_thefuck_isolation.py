"""EXP-009D-B: POST-HOC binary wheel isolation for TheFuck only.

Triggered by the previously observed failure of the preregistered
four-requirement probe. Does not change or rescore that original experiment.
No third-party code execution, builds, installs, or credentials passed to pip.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic

from .exp009d_wheels import (
    ROOT, PLAN, FILENAME, TIMEOUT_SECONDS, read_plan, wheel_digest,
)

OUTPUT = ROOT / "results" / "exp009d-thefuck-wheel-isolation.json"
SOURCE_RUN = "41804523888"
REQUIRED_CASE_IDS = ["thefuck-1", "thefuck-2", "thefuck-3"]


def validate_source():
    original = json.loads(
        (ROOT / "results" / "exp009d-wheel-summary.json").read_text(
            encoding="utf-8"))
    if (original.get("experiment") != "EXP-009D"
            or original.get("projects", [])[-1].get("project") != "thefuck"
            or original["projects"][-1].get("reason")
               != "binary_only_resolution_failed"
            or original["projects"][-1].get("cases") != REQUIRED_CASE_IDS
            or original.get("policy_scores_generated") != 0):
        raise ValueError("Original failed environment probe was modified")
    data = read_plan()
    reqs = data["projects"]["thefuck"]["requirements"]
    if len(reqs) != 4 or any("==" not in r for r in reqs):
        raise ValueError("Preselected direct dependency set modified")
    return list(reqs)


def sanitized_environment(home: str) -> dict:
    env = {k: os.environ[k] for k in (
        "PATH", "LANG", "LC_ALL", "TZ", "SSL_CERT_FILE")
        if k in os.environ}
    env.update({
        "HOME": home, "PIP_CONFIG_FILE": os.devnull,
        "PIP_NO_INPUT": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PYTHONNOUSERSITE": "1",
    })
    return env


def probe_one(requirement: str, *, runner=None) -> dict:
    reqs = validate_source()
    if requirement not in reqs:
        raise ValueError("Only TheFuck's four originally chosen pins")
    with TemporaryDirectory(prefix="exp009d-b-isolated-") as temp:
        cmd = [
            sys.executable, "-s", "-m", "pip", "download",
            "--only-binary=:all:", "--no-deps", "--no-cache-dir",
            "--disable-pip-version-check", "--no-input",
            "--timeout", "15", "--retries", "1",
            "--index-url", "https://pypi.org/simple",
            "--dest", temp, requirement,
        ]
        begin = monotonic()
        result = {
            "requirement": requirement, "status": "blocked",
            "blocker": None, "wheel_filename": None,
            "sha256": None, "wheel_bytes": 0, "seconds": None,
            "dependencies_installed": False, "upstream_imported": False,
        }
        try:
            proc = (runner or subprocess.run)(
                cmd, env=sanitized_environment(temp), check=False,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=min(TIMEOUT_SECONDS, 90))
            result["seconds"] = round(monotonic() - begin, 3)
            if proc.returncode != 0:
                result["blocker"] = "binary_only_no_deps_download_failed"
                return result
            files = sorted(x for x in Path(temp).iterdir() if x.is_file())
            if len(files) != 1 or not FILENAME.fullmatch(files[0].name):
                result["blocker"] = "wheel_metadata_missing_or_unexpected"
                return result
            wheel = files[0]
            result.update({
                "status": "single_wheel_downloaded",
                "wheel_filename": wheel.name,
                "sha256": wheel_digest(wheel),
                "wheel_bytes": wheel.stat().st_size,
            })
        except subprocess.TimeoutExpired:
            result["blocker"] = "download_timeout"
        except (OSError, ValueError):
            result["blocker"] = "local_probe_error"
        return result


def probe_all(*, runner=None, python_minor=None) -> dict:
    version = (".".join(str(v) for v in sys.version_info[:2])
               if python_minor is None else python_minor)
    required = validate_source()
    report = {
        "experiment": "EXP-009D-B",
        "phase": "explicitly_post_hoc_wheel_root_cause_triage",
        "origin_run": SOURCE_RUN,
        "origin_report": "results/exp009d-wheel-summary.json",
        "project": "thefuck",
        "cases_preserved": REQUIRED_CASE_IDS,
        "actual_python_minor": version,
        "historical_python": "3.7.0",
        "outcome_of_original_complete_probe": "blocked",
        "original_requirement_set_unchanged": True,
        "individual_probes": [],
        "classification": None,
        "upstream_tests_executed": 0,
        "policy_scores_generated": 0,
        "environment_complete": False,
    }
    if version != "3.7":
        report["classification"] = "invalid_python_minor"
        return report
    for dependency in required:
        report["individual_probes"].append(
            probe_one(dependency, runner=runner))
    if any(x["status"] == "blocked" for x in report["individual_probes"]):
        report["classification"] = "at_least_one_direct_binary_download_blocked"
    else:
        report["classification"] = "all_direct_binaries_available_full_resolution_still_blocked"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    if args.offline:
        print("EXP009D_B_PREFLIGHT=" + json.dumps({
            "requirements": validate_source(),
            "cases": REQUIRED_CASE_IDS,
            "no_tests_or_scores": True,
        }, sort_keys=True))
        return
    result = probe_all()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2,
                                 sort_keys=True) + "\n", encoding="utf-8")
    print("EXP009D_B_RESULT=" + json.dumps({
        "project": "thefuck", "classification": result["classification"],
        "per_dependency": [{"requirement": x["requirement"],
                            "status": x["status"], "blocker": x["blocker"]}
                           for x in result["individual_probes"]],
        "new_bug_scores": 0,
    }, sort_keys=True))
    if (result["actual_python_minor"] != "3.7"
            or len(result["individual_probes"]) != 4
            or result["cases_preserved"] != REQUIRED_CASE_IDS):
        raise SystemExit("Incomplete isolation experiment")


if __name__ == "__main__":
    main()
