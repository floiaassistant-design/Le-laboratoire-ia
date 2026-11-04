"""EXP-009B: read-only historical exception qualification; never rescoring.
Only use from isolated GitHub Actions jobs. No third-party code on user PC.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from .exception_diagnostics import capture_unittest, capture_pytest, redacted_view
from .real_bug_batch import load_manifest, runner_command, RUN_TIMEOUT
from .real_bug_priority import ROOT

CASES = {
    "youtube-dl-4": "test.test_jsinterp.TestJSInterpreter.test_call",
    "tornado-2": "tornado.test.httpclient_test.HTTPClientCommonTestCase.test_redirect_put_without_body",
    "tornado-3": None,
    "cookiecutter-1": "tests/test_generate_context.py::test_generate_context_decodes_non_ascii_chars",
}
PROJECTS = ("youtube-dl", "tornado", "cookiecutter")
MARKER = "EXP009B_CHILD="


def diagnostic_child(case_id: str) -> dict:
    cases = {item["id"]: item for item in load_manifest()["cases"]}
    if case_id not in CASES:
        raise ValueError("Only four previously audited cases are permitted")
    case = cases[case_id]
    root = Path.cwd().resolve()
    result = (capture_pytest(case["test_file"], root)
              if case["framework"] == "pytest"
              else capture_unittest(case["module"], root))
    focus = set() if CASES[case_id] is None else {CASES[case_id]}
    return redacted_view(result, focus)


def run_child(worktree: Path, case_id: str) -> dict:
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": os.pathsep.join((str(ROOT), str(worktree))),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONHASHSEED": "0",
        "HOME": str(worktree),
    })
    try:
        proc = subprocess.run(
            [sys.executable, "-B", "-s", "-m", "lab.exp009b_qualification",
             "--child-case", case_id],
            cwd=worktree, env=env, capture_output=True, text=True,
            errors="replace", timeout=RUN_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"valid": False, "reason": type(exc).__name__}
    # Do not copy stdout/stderr into reports. Boolean only for warning token.
    lines = [line[len(MARKER):] for line in proc.stdout.splitlines()
             if line.startswith(MARKER)]
    if proc.returncode != 0 or len(lines) != 1:
        return {"valid": False, "reason": "child_process_or_marker_failure"}
    try:
        result = json.loads(lines[0])
    except (ValueError, TypeError):
        return {"valid": False, "reason": "child_json_error"}
    if not isinstance(result, dict) or not result.get("valid"):
        return {"valid": False, "reason": "child_collection_or_execution_error"}
    result["stderr_warning_keyword_present"] = bool(re.search(
        r"warning|exception ignored", proc.stderr, flags=re.IGNORECASE))
    return result


def assess(case: dict, old_audit: dict, buggy: dict, fixed: dict) -> dict:
    """Classification is exploratory: no source bug is confirmed by type alone."""
    target = CASES[case["id"]]
    if target is not None and (target not in buggy["focus"]
                               or target not in fixed["focus"]):
        return {"case": case["id"], "project": case["project"],
                "status": "blocked", "reason": "declared_test_id_not_collected"}
    match = (buggy["counts"] == old_audit["status_counts_buggy"]
             and fixed["counts"] == old_audit["status_counts_fixed"])
    if target is None:
        return {
            "case": case["id"], "project": case["project"],
            "status": "qualified_exploratory",
            "historical_status_counts_match": match,
            "new_count_buggy": buggy["counts"], "new_count_fixed": fixed["counts"],
            "stderr_warning_keyword_buggy": buggy["stderr_warning_keyword_present"],
            "stderr_warning_keyword_fixed": fixed["stderr_warning_keyword_present"],
            "classification": "no_confirmed_witness_in_selected_suite",
            "caution": "No subprocess warning capture guarantee; cannot infer absence.",
        }
    if target not in buggy["focus"] or target not in fixed["focus"]:
        return {"case": case["id"], "project": case["project"],
                "status": "blocked", "reason": "declared_test_id_not_collected"}
    before, after = buggy["focus"][target], fixed["focus"][target]
    classification = (
        "unattributed_differential_exception"
        if (before["status"], after["status"]) == ("error", "pass")
        else "changed_or_unreproduced_not_attributed")
    detail = before["exception"]
    source_frame_seen = bool(detail and any(
        frame["file"] != case["test_file"]
        and not frame["file"].startswith("test/")
        and "/test/" not in frame["file"]
        and not frame["file"].startswith("tests/")
        for frame in detail["project_frames"]))
    return {
        "case": case["id"], "project": case["project"],
        "status": "qualified_exploratory",
        "historical_status_counts_match": match,
        "target_test_id": target,
        "buggy_status": before["status"], "fixed_status": after["status"],
        "exception": detail,
        "source_code_frame_present": source_frame_seen,
        "stderr_warning_keyword_buggy": buggy["stderr_warning_keyword_present"],
        "stderr_warning_keyword_fixed": fixed["stderr_warning_keyword_present"],
        "classification": classification,
        "caution": "Source frame or exception type alone cannot prove causality.",
    }


def qualify_project(project: str) -> dict:
    if project not in PROJECTS:
        raise ValueError("Unsupported project")
    manifest = load_manifest()
    selected = [c for c in manifest["cases"]
                if c["id"] in CASES and c["project"] == project]
    old = json.loads((ROOT / "results/exp009a-oracle-audit.json")
                     .read_text(encoding="utf-8"))
    audits = {c["case"]: c for c in old["cases"]}
    records = []
    with TemporaryDirectory(prefix="exp009b-") as temp:
        work = Path(temp)
        clone = work / "origin"
        try:
            runner_command(["git", "-c", "core.hooksPath=/dev/null", "clone",
                            "--quiet", "--filter=blob:none", "--no-checkout",
                            selected[0]["url"], str(clone)])
            clone_ok = True
        except (OSError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired):
            clone_ok = False
        for case in selected:
            if not clone_ok:
                records.append({"case": case["id"], "project": project,
                                "status": "blocked", "reason": "clone_failed"})
                continue
            try:
                parent = runner_command(["git", "-C", str(clone), "rev-parse",
                                         case["fixed"]+"^"],
                                        timeout=30).stdout.strip()
                if parent != case["buggy"]:
                    raise ValueError("pinned_git_parent_mismatch")
                before_root = work / (case["id"]+"-buggy")
                after_root = work / (case["id"]+"-fixed")
                for location, sha in ((before_root, case["buggy"]),
                                      (after_root, case["fixed"])):
                    runner_command(["git", "-c", "core.hooksPath=/dev/null",
                                    "-C", str(clone), "worktree", "add",
                                    "--quiet", "--detach", str(location), sha])
                license_text = (after_root/case["license_path"]).read_text(
                    encoding="utf-8")
                signatures = {"Unlicense": "unencumbered software",
                              "Apache-2.0": "Apache License",
                              "BSD-3-Clause": "Redistribution and use"}
                if signatures[case["license"]] not in license_text:
                    raise ValueError("license_mismatch")
                shutil.copyfile(after_root/case["test_file"],
                                before_root/case["test_file"])
                after = run_child(after_root, case["id"])
                before = run_child(before_root, case["id"])
                if not after.get("valid") or not before.get("valid"):
                    record = {"case": case["id"], "project": project,
                              "status": "blocked", "reason": "child_failed_or_incomplete"}
                else:
                    record = assess(case, audits[case["id"]], before, after)
            except (OSError, ValueError, KeyError, TypeError, UnicodeError,
                    subprocess.CalledProcessError, subprocess.TimeoutExpired):
                record = {"case": case["id"], "project": project,
                          "status": "blocked", "reason": "isolation_or_setup_failed"}
            records.append(record)
    return {
        "experiment": "EXP-009B", "status": "exploratory_no_rescoring",
        "source_case_manifest": "experiments/exp008b-manifest.json",
        "source_audit": "results/exp009a-oracle-audit.json",
        "project": project, "expected_case_count": len(selected),
        "case_count": len(records),
        "blocked_count": sum(r["status"] == "blocked" for r in records),
        "cases": records,
        "exp008b_scores_modified": False, "new_bugs_confirmed": 0,
        "new_model_calls": 0,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--project", choices=PROJECTS)
    choice.add_argument("--child-case", choices=CASES)
    args = parser.parse_args(argv)
    if args.child_case:
        print(MARKER + json.dumps(diagnostic_child(args.child_case),
                                  ensure_ascii=True, sort_keys=True))
        return
    result = qualify_project(args.project)
    path = ROOT / ("results/exp009b-"+args.project+"-diagnostics.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=True, indent=2)+"\n",
                    encoding="utf-8")
    print("EXP009B_SUMMARY=" + json.dumps({
        "project": result["project"], "cases": result["case_count"],
        "blocked": result["blocked_count"],
        "classifications": [c.get("classification", c.get("reason"))
                            for c in result["cases"]],
        "rescore": False,
    }, sort_keys=True))
    if result["case_count"] != result["expected_case_count"]:
        raise SystemExit("Missing preregistered historic case")


if __name__ == "__main__":
    main()
