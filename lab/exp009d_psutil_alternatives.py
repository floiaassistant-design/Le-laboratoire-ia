"""EXP-009D-C: explicitly POST-HOC alternative psutil binary feasibility.

The original four-project probe remains frozen and failed for TheFuck.
Only public binary wheel downloads, never upstream import/test/install/build.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic

from .exp009d_wheels import ROOT, FILENAME, wheel_digest

PLAN = ROOT / "experiments" / "exp009d-c-psutil-candidates.json"
ORIGINAL = ROOT / "results" / "exp009d-wheel-summary.json"
OUTPUT = ROOT / "results" / "exp009d-c-psutil-alternatives.json"
CANDIDATES = ["psutil==5.7.3", "psutil==5.8.0", "psutil==5.9.8"]
OTHER_PINS = ["pyte==0.8.0", "pytest==5.4.3", "pexpect==4.8.0"]
CASE_IDS = ["thefuck-1", "thefuck-2", "thefuck-3"]


def validate_plan():
    d = json.loads(PLAN.read_text(encoding="utf-8"))
    origin = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    match = [x for x in origin.get("projects", [])
             if x.get("project") == "thefuck"]
    if (d.get("experiment") != "EXP-009D-C"
            or d.get("phase") != "post_hoc_psutil_alternatives_binary_feasibility"
            or d.get("status") != "post_hoc_environment_calibration_no_bug_test"
            or d.get("project") != "thefuck" or d.get("python_minor") != "3.7"
            or d.get("original_fixed_requirement") != "psutil==5.6.7"
            or d.get("candidates_in_predeclared_order") != CANDIDATES
            or d.get("preserved_other_pins") != OTHER_PINS
            or d.get("case_ids") != CASE_IDS
            or d.get("allowed_index") != "https://pypi.org/simple"
            or d.get("scoring_disabled") is not True
            or d.get("package_source_exec") is not False
            or d.get("modified_original_manifests") is not False
            or d.get("selection_rule") !=
              "probe_all_three_in_order_with_no_deps; choose first successful direct-wheel candidate in listed order; then probe that replacement plus original remaining pins with dependencies"
            or len(match) != 1 or match[0].get("reason")
               != "binary_only_resolution_failed"
            or match[0].get("cases") != CASE_IDS
            or origin.get("policy_scores_generated") != 0):
        raise ValueError("Post-hoc environment experiment not preregistered")
    return d


def environment(folder):
    # Explicit allowlist: GitHub access tokens and global pip config omitted.
    env = {k: os.environ[k] for k in
           ("PATH", "LANG", "LC_ALL", "TZ", "SSL_CERT_FILE")
           if k in os.environ}
    env.update({"HOME": folder, "PIP_CONFIG_FILE": os.devnull,
                "PYTHONNOUSERSITE": "1", "PIP_NO_INPUT": "1",
                "PIP_DISABLE_PIP_VERSION_CHECK": "1"})
    return env


def download_binary(specs, *, resolve_dependencies, runner=None):
    plan = validate_plan()
    if (not isinstance(specs, list) or not specs
            or specs not in [[c] for c in CANDIDATES]
            and specs not in [[c] + OTHER_PINS for c in CANDIDATES]):
        raise ValueError("Only explicitly preselected binary wheel probes")
    with TemporaryDirectory(prefix="exp009d-c-wheels-") as folder:
        cmd = [
            sys.executable, "-s", "-m", "pip", "download",
            "--only-binary=:all:", "--no-cache-dir", "--no-input",
            "--disable-pip-version-check", "--timeout", "15",
            "--retries", "1", "--index-url", plan["allowed_index"],
            "--dest", folder,
        ]
        if not resolve_dependencies:
            cmd.append("--no-deps")
        cmd.extend(specs)
        started = monotonic()
        result = {
            "requirements": specs, "resolve_dependencies": resolve_dependencies,
            "status": "blocked", "blocker": None, "wheel_count": 0,
            "wheels": [], "seconds": None, "package_installed": False,
            "upstream_code_executed": False,
        }
        try:
            cp = (runner or subprocess.run)(
                cmd, env=environment(folder), timeout=130,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                check=False)
            result["seconds"] = round(monotonic() - started, 3)
            if cp.returncode:
                result["blocker"] = "binary_download_or_resolution_failed"
                return result
            files = sorted(p for p in Path(folder).iterdir() if p.is_file())
            if (not files or len(files) > 100 or
                    any(not FILENAME.fullmatch(p.name) for p in files)):
                result["blocker"] = "unexpected_wheel_directory_contents"
                return result
            result["wheels"] = [
                {"filename": x.name, "sha256": wheel_digest(x),
                 "bytes": x.stat().st_size} for x in files
            ]
            result["wheel_count"] = len(files)
            result["status"] = "wheels_downloaded_not_installed"
        except subprocess.TimeoutExpired:
            result["blocker"] = "download_timeout"
        except (OSError, ValueError):
            result["blocker"] = "local_download_error"
        return result


def evaluate(*, python_minor=None, runner=None):
    validate_plan()
    minor = (".".join(str(v) for v in sys.version_info[:2])
             if python_minor is None else python_minor)
    report = {
        "experiment": "EXP-009D-C",
        "phase": "post_hoc_environment_calibration",
        "case_ids_preserved": CASE_IDS,
        "original_requirement": "psutil==5.6.7",
        "original_result_unchanged": "blocked",
        "candidate_probes": [],
        "selected_candidate": None, "full_binary_probe": None,
        "python_minor": minor, "classification": None,
        "upstream_tests_executed": 0, "policy_scores": None,
        "environment_installation_proven": False,
        "semantics_equivalent_to_original": False,
        "hypothesis_selected_after_original_failure": True,
    }
    if minor != "3.7":
        report["classification"] = "invalid_python_minor"
        return report
    for pin in CANDIDATES:
        report["candidate_probes"].append(
            download_binary([pin], resolve_dependencies=False, runner=runner))
    viable = [
        pin for pin, item in zip(CANDIDATES, report["candidate_probes"])
        if item["status"] == "wheels_downloaded_not_installed"]
    if not viable:
        report["classification"] = "no_predeclared_alternative_direct_wheel"
        return report
    chosen = viable[0]  # earliest in immutable preregistered ordering
    report["selected_candidate"] = chosen
    report["full_binary_probe"] = download_binary(
        [chosen] + OTHER_PINS, resolve_dependencies=True, runner=runner)
    report["classification"] = (
        "alternate_complete_binary_set_downloaded_not_installed"
        if report["full_binary_probe"]["status"]
           == "wheels_downloaded_not_installed"
        else "alternate_combined_resolution_blocked")
    return report


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--offline", action="store_true")
    args = p.parse_args(argv)
    if args.offline:
        validate_plan()
        print("EXP009D_C_PLAN=" + json.dumps({
            "candidates": CANDIDATES, "selection": "first_available",
            "upstream_tests": 0, "scores": 0,
        }, sort_keys=True))
        return
    result = evaluate()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, sort_keys=True,
                                 indent=2)+"\n", encoding="utf-8")
    print("EXP009D_C_RESULT=" + json.dumps({
        "case_ids": result["case_ids_preserved"],
        "candidate_statuses": [
            {"requirement": c["requirements"][0], "status": c["status"],
             "blocker": c["blocker"]}
            for c in result["candidate_probes"]],
        "selected": result["selected_candidate"],
        "classification": result["classification"],
        "full_wheel_count": (result["full_binary_probe"] or {}).get(
            "wheel_count", 0),
        "tests": 0, "scores": 0,
    }, sort_keys=True))
    if (result["python_minor"] != "3.7"
            or len(result["candidate_probes"]) != 3
            or result["case_ids_preserved"] != CASE_IDS):
        raise SystemExit("Incomplete post-hoc alternative report")


if __name__ == "__main__":
    main()
