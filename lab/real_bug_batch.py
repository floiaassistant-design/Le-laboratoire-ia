"""EXP-008B: eight predeclared historical bugs, three independent projects.

Fixed policies are imported UNCHANGED from EXP-008A. This module never
inspects defects to rank tests. Same fixed-commit test file executes against
buggy and fixed code, so this is retrospective, never blind validation.

Third-party Python is imported and executed ONLY in GitHub Actions isolated
read-only runners, not on a user's computer. No model/API calls.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic

from .real_bug_priority import (
    ROOT, RecordingResult, _flatten, method_features, policy_orders,
    exact_random_hit,
)
import unittest

MANIFEST = ROOT / "experiments" / "exp008b-manifest.json"
MARKER = "EXP008B_CHILD="
RUN_TIMEOUT = 150
CLONE_TIMEOUT = 150
MAX_TESTS = 500
BUDGETS = (1, 3, 6, 12)
PROJECTS = ("youtube-dl", "tornado", "cookiecutter")


def load_manifest() -> dict:
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    validate_manifest(m)
    return m


def validate_manifest(m: dict) -> None:
    if (m.get("experiment") != "EXP-008B" or
        m.get("budgets") != list(BUDGETS) or
        m.get("seed") != 20261103 or
        m.get("policies") !=
        ["lexical", "seeded_random", "structural_diversity"]):
        raise ValueError("Frozen experiment configuration changed")
    cases = m.get("cases")
    expected = [("youtube-dl", 2), ("youtube-dl", 3), ("youtube-dl", 4),
                ("tornado", 2), ("tornado", 3), ("tornado", 4),
                ("cookiecutter", 1), ("cookiecutter", 2)]
    if not isinstance(cases, list) or len(cases) != len(expected):
        raise ValueError("All eight predeclared cases are required")
    urls = {"youtube-dl": "ytdl-org/youtube-dl",
            "tornado": "tornadoweb/tornado",
            "cookiecutter": "cookiecutter/cookiecutter"}
    for c, (name, n) in zip(cases, expected):
        if (c.get("project"), c.get("id")) != (name, f"{name}-{n}"):
            raise ValueError("Predeclared case order or identity changed")
        if c.get("repo") != urls[name] or c.get("url") != (
                "https://github.com/" + urls[name] + ".git"):
            raise ValueError("Unexpected external URL")
        if c.get("framework") != ("pytest" if name == "cookiecutter"
                                 else "unittest"):
            raise ValueError("Unexpected testing framework")
        if not all(isinstance(c.get(k), str) and
                   re.fullmatch(r"[0-9a-f]{40}", c[k])
                   for k in ("fixed", "buggy")):
            raise ValueError("All revisions must be immutable SHA-40")
        if c["fixed"] == c["buggy"]:
            raise ValueError("Bug and fix must differ")
        if not re.fullmatch(r"[A-Za-z0-9_./-]+\.py", c["test_file"]) or (
                ".." in Path(c["test_file"]).parts):
            raise ValueError("Unsafe test path")
    if m.get("test_source") != (
            "fixed revision test file overlaid into both pinned worktrees; "
            "historical fix-aware test bank"):
        raise ValueError("Test bank source modified")


def runner_command(cmd: list[str], *, cwd=None, timeout=CLONE_TIMEOUT):
    return subprocess.run(cmd, cwd=cwd, timeout=timeout, check=True,
                          capture_output=True, text=True, errors="replace")


def _capture_unittest(module: str) -> dict:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(module)
    tests = list(_flatten(suite))
    ids = [test.id() for test in tests]
    if loader.errors or not ids or len(ids) > MAX_TESTS or len(set(ids)) != len(ids):
        return {"valid": False, "reason": "invalid_unittest_collection",
                "collected": len(ids), "loader_error_count": len(loader.errors)}
    recording = RecordingResult()
    suite.run(recording)
    statuses = {key: recording.status.get(key, "missing") for key in sorted(ids)}
    return {"valid": all(status != "missing" for status in statuses.values()),
            "ids": sorted(ids),
            "statuses": statuses,
            "counts": dict(Counter(statuses.values())),
            "collected": len(ids),
            "executed": recording.testsRun}


def _capture_pytest(path: str) -> dict:
    import pytest

    class Capture:
        def __init__(self):
            self.ids = []
            self.statuses = {}
            self.missing_report_count = 0

        def pytest_collection_finish(self, session):
            self.ids = [item.nodeid for item in session.items]

        @pytest.hookimpl(hookwrapper=True)
        def pytest_runtest_makereport(self, item, call):
            result = yield
            report = result.get_result()
            if report.when == "call" and report.failed:
                report.lab_assertion = bool(
                    call.excinfo is not None and
                    isinstance(call.excinfo.value, AssertionError))

        def pytest_runtest_logreport(self, report):
            ident = report.nodeid
            if report.when == "setup":
                if report.failed:
                    self.statuses[ident] = "error"
                elif report.skipped:
                    self.statuses[ident] = "skip"
            elif report.when == "call":
                if report.passed:
                    self.statuses[ident] = "pass"
                elif report.skipped:
                    self.statuses[ident] = "skip"
                elif report.failed:
                    self.statuses[ident] = (
                        "fail" if getattr(report, "lab_assertion", False)
                        else "error")
            elif report.when == "teardown" and report.failed:
                self.statuses[ident] = "error"

    capture = Capture()
    # Both auto-loaded plugins and repo-level addopts can introduce
    # collection/execution beyond the frozen test-file path. Disable both.
    exit_code = pytest.main([path, "-q", "--tb=no", "--disable-warnings",
                             "-p", "no:cacheprovider", "-o", "addopts="],
                            plugins=[capture])
    ids = capture.ids
    if (int(exit_code) not in (0, 1) or not ids or len(ids) > MAX_TESTS
            or len(ids) != len(set(ids)) or
            set(ids) != set(capture.statuses)):
        return {"valid": False, "reason": "pytest_collection_or_execution_error",
                "pytest_exit_code": int(exit_code),
                "collected": len(ids),
                "report_count": len(capture.statuses)}
    return {"valid": True, "ids": sorted(ids),
            "statuses": {k: capture.statuses[k] for k in sorted(ids)},
            "counts": dict(Counter(capture.statuses.values())),
            "collected": len(ids),
            "executed": len(capture.statuses)}


def child_run(case_id: str) -> dict:
    cases = {case["id"]: case for case in load_manifest()["cases"]}
    if case_id not in cases:
        raise ValueError("Unknown or unregistered test module")
    case = cases[case_id]
    if case["framework"] == "pytest":
        return _capture_pytest(case["test_file"])
    return _capture_unittest(case["module"])


def child_process(root: Path, case_id: str) -> dict:
    env = os.environ.copy()
    # All Python source is loaded only from the isolated worktree, plus
    # our first-party harness. Never use stale .pyc or user site-packages.
    env.update({"PYTHONPATH":os.pathsep.join((str(ROOT), str(root))),
                "PYTHONDONTWRITEBYTECODE":"1",
                "PYTHONNOUSERSITE":"1",
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD":"1",
                "PYTHONHASHSEED":"0",
                "HOME":str(root)})
    began = monotonic()
    child = subprocess.run([sys.executable, "-B", "-s", "-m",
                            "lab.real_bug_batch", "--child-case", case_id],
                           cwd=root, env=env, capture_output=True, text=True,
                           errors="replace", timeout=RUN_TIMEOUT)
    lines = [line[len(MARKER):] for line in child.stdout.splitlines()
             if line.startswith(MARKER)]
    if child.returncode != 0 or len(lines) != 1:
        raise RuntimeError(
            "test child failed (exit=%s; stdout tail=%s; stderr tail=%s)" %
            (child.returncode, child.stdout[-250:], child.stderr[-550:]))
    result = json.loads(lines[0])
    if not result.get("valid"):
        raise RuntimeError("collect/run incomplete: "+repr(result)[:450])
    result["wall_seconds"] = round(monotonic()-began, 3)
    return result


def features_for_case(case: dict, code: str, ids: list[str]) -> dict:
    if case["framework"] == "unittest":
        return method_features(code, ids)
    # Pytest parametrized IDs include [param], which all share the same
    # static definition. Keep its AST features, while using *full* IDs
    # to resolve policy tie-breaks, without any execution outcomes.
    names = sorted({id_.split("::")[-1].split("[")[0] for id_ in ids})
    fn_features = method_features(code, names)
    return {id_: fn_features[id_.split("::")[-1].split("[")[0]]
            for id_ in ids}


def score_pair(case: dict, before: dict, after: dict,
               test_code: str, seed: int) -> dict:
    before_ids = before["ids"]
    after_ids = after["ids"]
    if before_ids != after_ids:
        raise ValueError("Buggy/fixed test universes differ")
    ids = after_ids
    if not ids:
        raise ValueError("No executable tests collected")
    if any(status in ("error", "missing", "started", "xpass")
           for status in after["statuses"].values()):
        raise ValueError("Corrected test-suite environment contains failures")
    tags = features_for_case(case, test_code, ids)
    orders = policy_orders(ids, tags, seed)
    exposing = {key:(before["statuses"][key] == "fail" and
                     after["statuses"][key] == "pass") for key in ids}
    changed_errors = {key:(before["statuses"][key] == "error" and
                           after["statuses"][key] == "pass") for key in ids}
    policy_results = {}
    for name, order in orders.items():
        policy_results[name] = {
            "first_12_ids": order[:12],
            "by_budget": {
                str(b):int(any(exposing[item] for item in
                               order[:min(b, len(order))]))
                for b in BUDGETS},
            "first_exposing_rank": next(
                (i+1 for i, key in enumerate(order) if exposing[key]), None)}
    return {
        "case": case["id"], "project":case["project"],
        "buggy_sha":case["buggy"], "fixed_sha":case["fixed"],
        "framework":case["framework"],
        "source_license":case["license"],
        "runtime_test_count":len(ids),
        "revealing_assertion_test_count":sum(exposing.values()),
        "revealing_ids":sorted(key for key, value in exposing.items() if value),
        "changed_error_not_counted":sum(changed_errors.values()),
        "fixed_status_counts":after["counts"],
        "buggy_status_counts":before["counts"],
        "fixed_wall_seconds":after["wall_seconds"],
        "buggy_wall_seconds":before["wall_seconds"],
        "effective_budgets":{str(b):min(b, len(ids)) for b in BUDGETS},
        "policies":policy_results,
        "exact_uniform_random_hit":{
            str(b):round(exact_random_hit(len(ids), sum(exposing.values()),
                                          min(b, len(ids))), 9)
            for b in BUDGETS},
        "all_test_statuses":{"fixed":after["statuses"],
                             "buggy":before["statuses"]},
        "test_statuses_observed_once_per_revision":True,
    }


def run_project(project: str) -> dict:
    data = load_manifest()
    if project not in PROJECTS:
        raise ValueError("Unknown predeclared project")
    selected=[c for c in data["cases"] if c["project"] == project]
    if not selected:
        raise ValueError("No cases for selected project")
    start=monotonic()
    outputs=[]
    with TemporaryDirectory(prefix="exp008b-"+project+"-") as work:
        base=Path(work)
        clone=base/"origin"
        # A failure to clone affects all predeclared cases, never removes them.
        clone_problem=None
        try:
            runner_command(["git", "-c", "core.hooksPath=/dev/null", "clone",
                            "--quiet", "--filter=blob:none", "--no-checkout",
                            selected[0]["url"], str(clone)])
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                OSError) as exc:
            clone_problem=type(exc).__name__ + ": " + str(exc)[-220:]
        for index, case in enumerate(selected):
            entry={"case":case["id"],"project":project,
                   "expected_sha":case["fixed"],
                   "status":"blocked","reason":None}
            if clone_problem:
                entry["reason"]="clone_error: "+clone_problem
                outputs.append(entry)
                continue
            try:
                found_index=next(i for i,c in enumerate(data["cases"])
                                 if c["id"]==case["id"])
                root_bug=base/(case["id"]+"-buggy")
                root_fixed=base/(case["id"]+"-fixed")
                parent=runner_command(["git","-C",str(clone),"rev-parse",
                                       case["fixed"]+"^"],timeout=30).stdout.strip()
                if parent!=case["buggy"]:
                    raise RuntimeError("Fixed commit parent is not buggy commit")
                for root, sha in ((root_bug,case["buggy"]),
                                  (root_fixed,case["fixed"])):
                    runner_command(["git", "-c", "core.hooksPath=/dev/null",
                                    "-C", str(clone), "worktree", "add",
                                    "--quiet", "--detach",str(root),sha])
                license_text=(root_fixed/case["license_path"]).read_text(
                    encoding="utf-8")
                license_checks={
                    "Unlicense":"unencumbered software",
                    "Apache-2.0":"Apache License",
                    "BSD-3-Clause":"Redistribution and use",
                }
                if license_checks[case["license"]] not in license_text:
                    raise RuntimeError("Historical project licence mismatch")
                src=root_fixed/case["test_file"]
                source=src.read_text(encoding="utf-8-sig")
                shutil.copyfile(src, root_bug/case["test_file"])
                after=child_process(root_fixed,case["id"])
                before=child_process(root_bug,case["id"])
                entry={"case":case["id"],"project":project,"status":"evaluated",
                       "result":score_pair(case,before,after,source,
                                           data["seed"]+found_index)}
            except (RuntimeError, ValueError, KeyError, OSError, UnicodeError,
                    subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                entry["reason"]=type(exc).__name__+": "+str(exc)[-550:]
            outputs.append(entry)
            # git worktrees remain in a TEMPORARY directory until job exit.
    return {"experiment":"EXP-008B","project":project,
            "study":"retroactive fixed-version test selection; not blinded",
            "source_manifest":"experiments/exp008b-manifest.json",
            "declared_case_count":len(selected),
            "evaluated_count":sum(x["status"]=="evaluated" for x in outputs),
            "blocked_count":sum(x["status"]=="blocked" for x in outputs),
            "cases":outputs,
            "project_wall_seconds":round(monotonic()-start,2),
            "models_used":0,"agents_used":0,
            "blocked_cases_are_not_assigned_zero_detection":True}


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--project",choices=PROJECTS)
    parser.add_argument("--child-case")
    parser.add_argument("--output",default=None)
    args=parser.parse_args(argv)
    if bool(args.project) == bool(args.child_case):
        parser.error("Specify --project or --child-case")
    if args.child_case:
        print(MARKER+json.dumps(child_run(args.child_case),ensure_ascii=True))
        return
    result=run_project(args.project)
    output=ROOT/(args.output or
                 "results/exp008b-"+args.project+"-raw.json")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    print("EXP008B_RESULT="+json.dumps({
        "project":result["project"],
        "declared":result["declared_case_count"],
        "evaluated":result["evaluated_count"],
        "blocked":result["blocked_count"],
        "cases":[{
            "case":c["case"],"status":c["status"],
            "reason":c.get("reason"),
            "n":c.get("result",{}).get("runtime_test_count"),
            "d":c.get("result",{}).get("revealing_assertion_test_count"),
            "ranks":{k:v["first_exposing_rank"] for k,v in
                     c.get("result",{}).get("policies",{}).items()},
            "score12":{k:v["by_budget"]["12"] for k,v in
                       c.get("result",{}).get("policies",{}).items()},
        } for c in result["cases"]]},
        ensure_ascii=False))
    if len(result["cases"])!=result["declared_case_count"]:
        raise SystemExit("Missing declared case in report")


if __name__=="__main__":
    main()
