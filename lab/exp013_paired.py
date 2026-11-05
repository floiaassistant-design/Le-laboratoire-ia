"""EXP-013: predeclared, model-free paired analysis of EXP-011 manual trials.

A complete trial record does not prove that separate ChatGPT sessions existed.
Statistical claims are explicitly out of scope for this small public benchmark.
The CLI recomputes EXP-011 scoring only after verifying the entire pinned
GSM8K blob, local question packet, and local private key.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from math import isfinite
from pathlib import Path

from .exp010a_adaptive import POLICIES
from .exp011_manual import (
    CALIBRATION, EVALUATION, PLAN, SOURCE_BLOB,
    load_json, make_packet_data, read_pinned_source, save_json,
    score, verify_prepared_files,
)

SCORED = frozenset(("correct", "incorrect", "abstained"))
KNOWN_FAILURE = frozenset(("incorrect", "abstained", "blocked_by_design",
                           "malformed_response"))
PENDING = frozenset(("unobserved_or_incomplete",
                     "missing_model_provenance", "nonindependent_sessions"))
KNOWN = frozenset(("correct",)) | KNOWN_FAILURE
STATUS_SET = KNOWN | PENDING
FIELDS = frozenset((
    "task_id", "split", "policy", "route", "status",
    "role_calls_self_reported", "elapsed_seconds_self_reported",
    "input_tokens_self_reported", "output_tokens_self_reported",
))
METRICS = ("elapsed_seconds_self_reported",
           "input_tokens_self_reported", "output_tokens_self_reported")


def _identities(indices):
    return tuple("gsm8k-test-" + str(i).zfill(4) for i in indices)


def _valid_metric(name, value):
    if value is None:
        return True
    if isinstance(value, bool):
        return False
    if name == "elapsed_seconds_self_reported":
        return isinstance(value, (int, float)) and isfinite(value) and 0 <= value <= 1_000_000
    return isinstance(value, int) and 0 <= value <= 1_000_000


def validate_graded(graded: dict) -> dict:
    """Reject alien/duplicated trials and internally inconsistent data.

    This alone does NOT verify source or session provenance. The CLI also
    reconstructs the graded data from original pinned files.
    """
    if (not isinstance(graded, dict) or graded.get("experiment") != "EXP-011"
            or graded.get("phase") != "manual_trials_only"
            or graded.get("independent_holdout_claim") is not False
            or graded.get("public_benchmark_training_contamination_possible") is not True
            or graded.get("model_execution_proof") !=
               "not_verifiable_from_self_reported_logs"):
        raise ValueError("Only the frozen EXP-011 manual report is supported")
    entries = graded.get("evaluations")
    all_ids = _identities(CALIBRATION) + _identities(EVALUATION)
    expected = {(id_, p) for id_ in all_ids for p in POLICIES}
    if not isinstance(entries, list) or len(entries) != len(expected):
        raise ValueError("EXP-011 trial roster must retain all 64 entries")
    lookup = {}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != FIELDS:
            raise ValueError("Unexpected graded trial structure")
        pair = entry["task_id"], entry["policy"]
        if pair not in expected or pair in lookup:
            raise ValueError("Missing, duplicate, or foreign task/policy pair")
        split = "calibration" if entry["task_id"] in _identities(CALIBRATION) else "evaluation"
        if entry["split"] != split:
            raise ValueError("Calibration/evaluation split was changed")
        status, route = entry["status"], entry["route"]
        if status not in STATUS_SET or route not in ("single", "parallel", "review", "blocked"):
            raise ValueError("Unexpected status or route")
        calls = entry["role_calls_self_reported"]
        if type(calls) is not int or not 0 <= calls <= (1 if route == "single" else 2):
            raise ValueError("Invalid role-call count")
        if route == "blocked":
            if status != "blocked_by_design" or calls != 0:
                raise ValueError("Blocked route has fabricated model calls")
        else:
            if status == "blocked_by_design":
                raise ValueError("Nonblocked route cannot be blocked by design")
            required = 1 if route == "single" else 2
            if status in SCORED | frozenset(("malformed_response",
                                             "missing_model_provenance",
                                             "nonindependent_sessions")) and calls != required:
                raise ValueError("Completed trial has missing role calls")
            if status == "unobserved_or_incomplete" and calls >= required:
                raise ValueError("Complete role roster cannot be called incomplete")
        if any(not _valid_metric(name, entry[name]) for name in METRICS):
            raise ValueError("Invalid self-reported metrics")
        lookup[pair] = entry
    if set(lookup) != expected:
        raise ValueError("Missing expected trials")
    reported = graded.get("real_model_results_recorded")
    actual = sum(e["status"] in SCORED for e in entries)
    if type(reported) is not int or reported != actual:
        raise ValueError("Reported observation count disagrees with roster")
    return lookup


def _interval(status: str) -> tuple[int, int]:
    if status == "correct":
        return (1, 1)
    if status in PENDING:
        return (0, 1)
    return (0, 0)


def _policy_metrics(entries: list[dict]) -> dict:
    total = len(entries)
    statuses = Counter(e["status"] for e in entries)
    correct = statuses["correct"]
    answered = correct + statuses["incorrect"]
    unknown = sum(statuses[s] for s in PENDING)
    observed = sum(statuses[s] for s in SCORED)
    nonblocked = [e for e in entries if e["route"] != "blocked"]
    metrics = {}
    for name in METRICS:
        measured = [e[name] for e in nonblocked if e[name] is not None]
        metrics[name.removesuffix("_self_reported")] = {
            "reported_trials": len(measured),
            "eligible_nonblocked_trials": len(nonblocked),
            "total_if_all_reported": (
                sum(measured) if nonblocked and len(measured) == len(nonblocked)
                else None
            ),
            "units": ("seconds" if name == "elapsed_seconds_self_reported" else "tokens"),
            "self_reported_only": True,
        }
    return {
        "tasks_assigned": total,
        "status_counts": {s: statuses[s] for s in sorted(STATUS_SET)},
        "scored_complete": observed,
        "unknown_or_invalid_provenance": unknown,
        "correct_answers": correct,
        "answers_delivered": answered,
        "answer_accuracy_when_answered": correct / answered if answered else None,
        "answer_coverage_per_assigned_task": answered / total,
        "task_success_fraction_lower_bound": correct / total,
        "task_success_fraction_upper_bound": (correct + unknown) / total,
        "recorded_role_calls_self_reported": sum(
            e["role_calls_self_reported"] for e in entries),
        "self_reported_resource_metrics": metrics,
        "has_scored_model_outputs": observed > 0,
    }


def _paired(evaluation: dict, baseline: str) -> dict:
    ids = _identities(EVALUATION)
    known_pairs = 0
    adaptive_only, baseline_only, both, neither = 0, 0, 0, 0
    lower_units, upper_units = 0, 0
    for task_id in ids:
        a = evaluation[(task_id, "adaptive")]["status"]
        b = evaluation[(task_id, baseline)]["status"]
        a_low, a_high = _interval(a)
        b_low, b_high = _interval(b)
        lower_units += a_low - b_high
        upper_units += a_high - b_low
        if a in KNOWN and b in KNOWN:
            known_pairs += 1
            if a == "correct" and b == "correct":
                both += 1
            elif a == "correct":
                adaptive_only += 1
            elif b == "correct":
                baseline_only += 1
            else:
                neither += 1
    return {
        "baseline": baseline,
        "assigned_paired_tasks": len(ids),
        "pairs_with_known_operational_outcomes": known_pairs,
        "pairs_with_missing_or_invalid_status": len(ids) - known_pairs,
        "adaptive_only_correct": adaptive_only,
        "baseline_only_correct": baseline_only,
        "both_correct": both,
        "neither_correct": neither,
        "delta_success_on_known_pairs": (
            (adaptive_only - baseline_only) / known_pairs if known_pairs else None),
        "delta_success_over_all_tasks_bounds": {
            "lower": lower_units / len(ids),
            "upper": upper_units / len(ids),
            "kind": "deterministic_missing-data_bounds_not_confidence_interval",
        },
        "inferential_p_value": None,
    }


def analyze(graded: dict) -> dict:
    roster = validate_graded(graded)
    by_split = {}
    for split, indices in (("calibration", CALIBRATION),
                           ("evaluation", EVALUATION)):
        by_split[split] = {
            policy: _policy_metrics(
                [roster[(task_id, policy)] for task_id in _identities(indices)])
            for policy in POLICIES
        }
    paired = {
        baseline: _paired(roster, baseline)
        for baseline in POLICIES if baseline != "adaptive"
    }
    evaluation_complete = all(
        x["unknown_or_invalid_provenance"] == 0
        for x in by_split["evaluation"].values()
    )
    return {
        "experiment": "EXP-013",
        "phase": "preregistered_non_inferential_paired_manual_analysis",
        "derived_from": "EXP-011_recomputed_after_pinned_source_verification",
        "source_blob_sha": SOURCE_BLOB,
        "calibration_tasks": len(CALIBRATION),
        "evaluation_tasks": len(EVALUATION),
        "policies": list(POLICIES),
        "primary_comparisons": "evaluation_only",
        "model_calls_made_by_analysis": 0,
        "reported_model_observations_exp011": graded["real_model_results_recorded"],
        "model_execution_provenance_attested": False,
        "chat_session_independence_attested": False,
        "same_model_comparability_verified": False,
        "model_labels_mixed_self_reported": graded.get("mixed_model_label_warning"),
        "known_public_dataset_training_contamination_possible": True,
        "confidence_intervals_or_statistical_significance_claimed": False,
        "all_evaluation_trials_have_known_operational_outcomes": evaluation_complete,
        "experimental_model_comparison_scientifically_proven": False,
        "cohorts": by_split,
        "adaptive_vs_baselines": paired,
        "interpretation": (
            "Observed answer accuracy is conditional on delivered numeric answers. "
            "Missing sessions, absent provenance and reused contexts are unknown "
            "rather than model errors. Abstentions, malformed outputs and "
            "policy blockages are known non-success for delivery. "
            "Bounds are logical missing-data limits, not confidence intervals. "
            "Role calls/tokens/latency are self-reported, not billable costs. "
            "There is no independence or generalization claim."
        ),
    }


def preflight() -> dict:
    """Synthetic packet of missing replies: no real benchmark results."""
    plan_raw = PLAN.read_bytes()
    plan = json.loads(plan_raw)
    rows = [{"question": "Synthetic " * 44 + "question?",
             "answer": "Synthetic gold for testing only.\n#### 42"}
            for _ in range(1319)]
    packets, key, responses = make_packet_data(
        rows, plan, hashlib.sha256(plan_raw).hexdigest())
    result = analyze(score(packets, key, responses))
    if result["reported_model_observations_exp011"] != 0:
        raise AssertionError("Preflight must have zero scored model outputs")
    result["phase"] = "synthetic_empty_response_preflight_no_models"
    result["not_a_real_experimental_result"] = True
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    cmds = parser.add_subparsers(dest="command", required=True)
    p = cmds.add_parser("preflight")
    p.add_argument("--report", default="results/exp013-analysis-preflight.json")
    p = cmds.add_parser("analyze")
    p.add_argument("--source", required=True, help="Exact official pinned GSM8K JSONL")
    p.add_argument("--out-dir", required=True, help="Private EXP-011 packet and responses")
    p.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    if args.command == "preflight":
        result = preflight()
    else:
        plan = load_json(PLAN)
        rows = read_pinned_source(Path(args.source).read_bytes(), plan)
        out = Path(args.out_dir)
        packets = load_json(out / "questions.json")
        key = load_json(out / "ANSWER-KEY-PRIVATE.json")
        verify_prepared_files(rows, plan, packets, key)
        graded = score(packets, key, load_json(out / "responses.json"))
        result = analyze(graded)
    dest = Path(args.report)
    dest.parent.mkdir(parents=True, exist_ok=True)
    save_json(dest, result)
    print("EXP013_ANALYSIS_MODEL_CALLS=0; scored_results=" +
          str(result["reported_model_observations_exp011"]))


if __name__ == "__main__":
    main()
