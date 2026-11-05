"""EXP-011C: offline provenance audit for human-reported EXP-011/011B trials.

No model, network, gold answer, or score is used. Duplicate *self-reported*
chat references are warnings about possible contamination, not proof of it.
Unique references are not proof of independent contexts either.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path

from .exp010a_adaptive import POLICIES
from .exp011_manual import (
    PLAN, ROLES, load_json, read_pinned_source, verify_prepared_files,
)
from .exp011_runbook import make_runbook

METRICS = ("elapsed_seconds", "input_tokens", "output_tokens")
EXPECTED_FIELDS = {
    "task_id", "policy", "model_label", "outputs", "sessions",
    "elapsed_seconds", "input_tokens", "output_tokens",
}


def _validate_record(record: dict, required: tuple[str, ...]) -> None:
    if not isinstance(record, dict) or set(record) != EXPECTED_FIELDS:
        raise ValueError("Unexpected response record fields")
    if not isinstance(record["outputs"], dict) or set(record["outputs"]) != set(ROLES):
        raise ValueError("Invalid role outputs")
    if not isinstance(record["sessions"], dict) or set(record["sessions"]) != set(ROLES):
        raise ValueError("Invalid role sessions")
    label = record["model_label"]
    if label is not None and (
        not isinstance(label, str) or not 1 <= len(label) <= 100
    ):
        raise ValueError("Invalid model label")
    for metric in METRICS:
        number = record[metric]
        if number is None:
            continue
        if (isinstance(number, bool) or not isinstance(number, (int, float))
                or not math.isfinite(number) or not 0 <= number <= 1_000_000):
            raise ValueError("Invalid metric")
        if metric != "elapsed_seconds" and not isinstance(number, int):
            raise ValueError("Token counts must be integers")
    for role in ROLES:
        output, session = record["outputs"][role], record["sessions"][role]
        if output is not None and (not isinstance(output, str) or len(output) > 200):
            raise ValueError("Invalid model output")
        if session is not None and (
            not isinstance(session, str) or not 1 <= len(session) <= 128
        ):
            raise ValueError("Invalid chat reference")
        if (output is None) != (session is None):
            raise ValueError("Output and chat reference must be provided together")
        if role not in required and (output is not None or session is not None):
            raise ValueError("A role not selected by the frozen route was populated")


def audit(packets: dict, runbook: dict, responses: dict) -> dict:
    """Audit exactly 64 planned trials, without inspecting answer correctness.

    The exact runbook and question fingerprints are checked against the frozen
    EXP-011/011B *plan*. For actual upstream-byte verification, the CLI uses
    the pinned source and validates the private key in memory first.
    """
    if runbook != make_runbook(packets):
        raise ValueError("Runbook differs from frozen planning")
    if not isinstance(responses, dict) or (
        responses.get("experiment") != "EXP-011"
        or responses.get("kind") != "self_reported_manual_record_template"
        or responses.get("plan_sha256") != packets["plan_sha256"]
    ):
        raise ValueError("Unrecognized response template")
    records = responses.get("records")
    trials = runbook["trials"]
    if not isinstance(records, list) or len(records) != len(trials) or len(trials) != 64:
        raise ValueError("All 64 trials must remain present")
    expected = {(t["task_id"], t["policy"]): t for t in trials}
    indexed = {}
    occurrences = defaultdict(list)
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Invalid record")
        pair = record.get("task_id"), record.get("policy")
        if pair not in expected or pair in indexed:
            raise ValueError("Missing, duplicate or foreign task/policy")
        trial = expected[pair]
        required = tuple(s["role"] for s in trial["steps"])
        _validate_record(record, required)
        indexed[pair] = record
        for role in required:
            session = record["sessions"][role]
            if session is not None:
                occurrences[session].append((trial["trial_id"], role))
    if set(indexed) != set(expected):
        raise ValueError("Incomplete roster")
    repeats = {
        ref: positions for ref, positions in occurrences.items()
        if len(positions) > 1
    }
    affected_trials = {
        trial_id
        for positions in repeats.values()
        for trial_id, _role in positions
    }
    rows = []
    labels = set()
    for trial in trials:
        rec = indexed[(trial["task_id"], trial["policy"])]
        required = tuple(s["role"] for s in trial["steps"])
        n = sum(rec["outputs"][role] is not None for role in required)
        if n and rec["model_label"]:
            labels.add(rec["model_label"])
        if trial["route"] == "blocked":
            status = "blocked_by_design"
        elif n == 0:
            status = "unobserved"
        elif n < len(required):
            status = "partial"
        elif not rec["model_label"]:
            status = "missing_model_label"
        elif trial["trial_id"] in affected_trials:
            status = "reused_session_reference"
        else:
            status = "complete_self_reported"
        rows.append({
            "trial_id": trial["trial_id"],
            "split": trial["split"], "policy": trial["policy"],
            "route": trial["route"], "status": status,
            "roles_planned": len(required),
            "roles_reported": n,
            "has_reused_session_reference": trial["trial_id"] in affected_trials,
            "metrics_reported": {
                metric: rec[metric] is not None for metric in METRICS
            },
        })
    summary = []
    for split in ("calibration", "evaluation"):
        for policy in POLICIES:
            group = [r for r in rows if r["split"] == split and r["policy"] == policy]
            counts = Counter(r["status"] for r in group)
            summary.append({
                "split": split, "policy": policy, "trials_total": len(group),
                "status_counts": dict(sorted(counts.items())),
                "roles_reported": sum(r["roles_reported"] for r in group),
                "trials_with_reused_reference": sum(
                    r["has_reused_session_reference"] for r in group
                ),
                "trials_with_metric": {
                    metric: sum(r["metrics_reported"][metric] for r in group)
                    for metric in METRICS
                },
            })
    return {
        "experiment": "EXP-011C",
        "phase": "manual_provenance_audit_no_model_execution",
        "planned_trials": 64,
        "observations_from_self_reported_records_only": True,
        "model_calls_performed_by_audit": 0,
        "answer_key_accessed_by_audit_function": False,
        "independence_verified": False,
        "chronological_order_verified": False,
        "same_model_verified": False,
        "quality_or_accuracy_evaluated": False,
        "unique_session_reference_is_not_proof_of_isolation": True,
        "distinct_model_labels_self_reported": len(labels),
        "mixed_model_label_warning": len(labels) > 1,
        "duplicated_session_references_count": len(repeats),
        "trials_affected_by_reuse": len(affected_trials),
        "summary": summary,
        "trials": rows,
    }


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Pinned GSM8K test.jsonl")
    parser.add_argument("--out-dir", required=True, help="Local private EXP-011 directory")
    parser.add_argument("--report", required=True, help="Report path (no raw outputs)")
    args = parser.parse_args(argv)
    out = Path(args.out_dir)
    plan = load_json(PLAN)
    rows = read_pinned_source(Path(args.source).read_bytes(), plan)
    packets = load_json(out / "questions.json")
    key = load_json(out / "ANSWER-KEY-PRIVATE.json")
    verify_prepared_files(rows, plan, packets, key)
    book = load_json(out / "manual-runbook.json")
    response = load_json(out / "responses.json")
    report = audit(packets, book, response)
    target = Path(args.report)
    if target.exists():
        raise ValueError("Refusing to overwrite an existing audit report")
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2,
                                 sort_keys=True) + "\n", encoding="utf-8")
    print("EXP011C_AUDIT=64 trials; " +
          str(report["trials_affected_by_reuse"]) + " reuse-risk trials; 0 model calls")


if __name__ == "__main__":
    main()
