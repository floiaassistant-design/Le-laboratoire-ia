"""EXP-009A: read-only oracle audit of EXP-008B raw observations.

No bug code import, no rerunning tests, no strategy ranking and NO change to
EXP-008B detection scores. Treat ERROR->PASS as an *unattributed signal*,
not a confirmed bug. Works with already archived per-project JSON files.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .real_bug_priority import ROOT

COHORT = (
    "youtube-dl-2", "youtube-dl-3", "youtube-dl-4",
    "tornado-2", "tornado-3", "tornado-4",
    "cookiecutter-1", "cookiecutter-2",
)
TARGETS = ("youtube-dl-4", "tornado-2", "tornado-3", "cookiecutter-1")
VALID_STATES = frozenset(("pass", "fail", "error", "skip", "xfail", "xpass"))


def _digest(mapping: dict) -> str:
    serialized = json.dumps(mapping, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def audit_case(entry: dict) -> dict:
    case = entry["case"]
    if entry["status"] == "blocked":
        return {"case":case, "status":"blocked",
                "blocker":entry.get("reason"), "oracle_audited":False}
    if entry["status"] != "evaluated" or "result" not in entry:
        raise ValueError("Invalid case state")
    r = entry["result"]
    observations = r["all_test_statuses"]
    buggy, fixed = observations["buggy"], observations["fixed"]
    if not buggy or set(buggy) != set(fixed):
        raise ValueError("Buggy and fixed test identities must be equal and nonempty")
    if any(x not in VALID_STATES for x in list(buggy.values()) + list(fixed.values())):
        raise ValueError("Unexpected test status")
    for name, statuses in (("buggy", buggy), ("fixed", fixed)):
        if len(statuses) != r["runtime_test_count"]:
            raise ValueError("Test count differs from EXP-008B")
        if dict(Counter(statuses.values())) != r[name+"_status_counts"]:
            raise ValueError("Per-version status counts differ from EXP-008B")
    transitions = [
        {"test_id":key, "buggy":buggy[key], "fixed":fixed[key]}
        for key in sorted(buggy) if buggy[key] != fixed[key]
    ]
    fail_to_pass = [x for x in transitions
                    if x["buggy"] == "fail" and x["fixed"] == "pass"]
    error_to_pass = [x for x in transitions
                     if x["buggy"] == "error" and x["fixed"] == "pass"]
    if len(fail_to_pass) != r["revealing_assertion_test_count"]:
        raise ValueError("Primary EXP-008B assertion score changed")
    if len(error_to_pass) != r["changed_error_not_counted"]:
        raise ValueError("EXP-008B error observations changed")
    if sorted(x["test_id"] for x in fail_to_pass) != sorted(r["revealing_ids"]):
        raise ValueError("EXP-008B primary revealing IDs changed")
    classification = ("strict_assertion_witness_exists" if fail_to_pass
                      else "unattributed_exception_to_pass" if error_to_pass
                      else "other_status_difference" if transitions
                      else "no_status_difference_in_chosen_test_file")
    return {
        "case":case,
        "project":entry["project"],
        "status":"evaluated",
        "oracle_audited":True,
        "classification":classification,
        "test_count":len(buggy),
        "status_counts_buggy":dict(sorted(Counter(buggy.values()).items())),
        "status_counts_fixed":dict(sorted(Counter(fixed.values()).items())),
        "status_map_sha256_buggy":_digest(buggy),
        "status_map_sha256_fixed":_digest(fixed),
        "observed_transition_count":len(transitions),
        "strict_assertion_fail_to_pass":len(fail_to_pass),
        "exception_error_to_pass_not_confirmed":len(error_to_pass),
        "changed_tests":transitions,
        "all_pass_in_both_versions":
            all(buggy[k]=="pass" and fixed[k]=="pass" for k in buggy),
    }


def audit_reports(reports: list[dict], *, require_complete: bool = False) -> dict:
    cases = {}
    projects = set()
    for raw in reports:
        if raw.get("experiment") != "EXP-008B":
            raise ValueError("Unexpected source experiment")
        project = raw["project"]
        if project in projects:
            raise ValueError("Duplicate project report")
        projects.add(project)
        for entry in raw["cases"]:
            case = entry["case"]
            if case in cases or case not in COHORT or entry["project"] != project:
                raise ValueError("Unexpected or duplicated case")
            cases[case] = audit_case(entry)
        if (len(raw["cases"]) != raw["declared_case_count"] or
            sum(x["status"]=="evaluated" for x in raw["cases"]) !=
                raw["evaluated_count"] or
            sum(x["status"]=="blocked" for x in raw["cases"]) !=
                raw["blocked_count"]):
            raise ValueError("EXP-008B declared counts inconsistent")
    if require_complete and set(cases) != set(COHORT):
        raise ValueError("All eight preregistered cases must be present")
    if not cases:
        raise ValueError("No cases audited")
    ordered = [cases[c] for c in COHORT if c in cases]
    focused = [cases[c] for c in TARGETS if c in cases]
    return {
        "experiment":"EXP-009A",
        "status":"audit_only_no_rescoring",
        "source_experiment":"EXP-008B",
        "source_raw_artifacts":"GitHub Actions run 41690471790 (3 project raw files)",
        "project_count":len(projects),
        "case_count":len(ordered),
        "cases":ordered,
        "four_predeclared_nonrevealing_cases":focused,
        "target_cases_present":len(focused),
        "target_error_to_pass_case_count":
            sum(x.get("exception_error_to_pass_not_confirmed",0)>0 for x in focused),
        "target_no_difference_case_count":
            sum(x.get("classification")=="no_status_difference_in_chosen_test_file"
                for x in focused),
        "primary_detection_rule_unchanged":True,
        "error_to_pass_is_confirmed_bug":False,
        "test_methods_rerun":False,
        "agents_or_models_evaluated":0,
        "warning":"Test status transitions alone do not prove root cause. "
                  "ERROR can be a real bug symptom or an environment error. "
                  "No retrospective adjustment of EXP-008B detection scores."
    }


def main(argv=None) -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",action="append",required=True)
    parser.add_argument("--output",default="results/exp009a-audit.json")
    parser.add_argument("--require-complete",action="store_true")
    args=parser.parse_args(argv)
    raw=[json.loads(Path(p).read_text(encoding="utf-8"))
         for p in args.input]
    audited=audit_reports(raw,require_complete=args.require_complete)
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(audited,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    print("EXP009A_ORACLE_AUDIT="+json.dumps({
        "cases":audited["case_count"],
        "targets":audited["target_cases_present"],
        "error_to_pass":audited["target_error_to_pass_case_count"],
        "no_difference":audited["target_no_difference_case_count"],
        "blocked":sum(c["status"]=="blocked" for c in audited["cases"]),
        "rescore":False
    },ensure_ascii=False))


if __name__=="__main__":
    main()
