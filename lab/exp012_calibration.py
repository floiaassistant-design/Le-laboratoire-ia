"""EXP-012: offline calibration scorer for self-reported single-chat replies.

No model is invoked. Calibration only; never rescore EXP-011 evaluations.
A public benchmark and a single shared context are NOT a scientific
comparison of agent orchestration.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from .exp011_manual import (
    CALIBRATION, PLAN, SOURCE_BLOB, SOURCE_COMMIT,
    normalized_number, read_pinned_source,
)

EXPECTED_IDS = tuple("gsm8k-test-" + str(i).zfill(4) for i in CALIBRATION)


def grade_rows(rows: list, observed: dict) -> dict:
    """Grade only four predetermined calibration indices; never return gold."""
    if (not isinstance(rows, list) or len(rows) != 1319
            or not isinstance(observed, dict)
            or observed.get("experiment") != "EXP-012"
            or observed.get("phase") != "raw_outputs_frozen_before_oracle"
            or observed.get("source_revision") != SOURCE_COMMIT
            or observed.get("source_blob_sha") != SOURCE_BLOB
            or observed.get("split") != "calibration"
            or observed.get("task_indices_base0") != list(CALIBRATION)
            or observed.get("session_independent") is not False
            or observed.get("provenance_attested") is not False
            or observed.get("oracle_correctness_at_time_of_commit") is not None
            or not isinstance(observed.get("model_label_self_reported"), str)
            or not observed["model_label_self_reported"].strip()):
        raise ValueError("Unfrozen, noncalibration, or falsely verified observations")
    answers = observed.get("answers")
    if not isinstance(answers, list) or len(answers) != 4:
        raise ValueError("All four calibration trials are required")
    if [x.get("task_id") for x in answers if isinstance(x, dict)] != list(EXPECTED_IDS):
        raise ValueError("Question identities changed or entries missing")

    evaluations = []
    for index, rec, task_id in zip(CALIBRATION, answers, EXPECTED_IDS):
        if set(rec) != {"task_id", "output"}:
            raise ValueError("Unexpected response fields")
        output = rec["output"]
        if output is not None and (not isinstance(output, str) or len(output) > 200):
            raise ValueError("Invalid response")
        gold_line = rows[index]["answer"].splitlines()[-1]
        gold = Decimal(normalized_number(gold_line, expected=True))
        if output is None:
            status = "unanswered"
        else:
            try:
                prediction = Decimal(normalized_number(output))
            except ValueError:
                status = "malformed"
            else:
                status = "correct" if prediction == gold else "incorrect"
        evaluations.append({"task_id": task_id, "status": status})
    statuses = {kind: sum(x["status"] == kind for x in evaluations)
                for kind in ("correct", "incorrect", "unanswered", "malformed")}
    assert sum(statuses.values()) == 4
    return {
        "experiment": "EXP-012",
        "phase": "exploratory_single_context_calibration_only",
        "source_blob_sha": SOURCE_BLOB,
        "calibration_cases_total": 4,
        "correct": statuses["correct"],
        "accuracy_over_all_four": statuses["correct"] / 4,
        "status_counts": statuses,
        "evaluations": evaluations,
        "model_provenance": "assistant_self_report_only",
        "fresh_contexts_verified": False,
        "model_orchestration_compared": False,
        "independent_holdout_claim": False,
        "model_calls_automated_by_scorer": 0,
        "training_contamination_possible": True,
        "notes": ("Same-chat exploratory arithmetic calibration on known public GSM8K "
                  "examples; not a multi-agent benchmark or model performance claim."),
    }


def score_pinned_source(payload: bytes, observed: dict) -> dict:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    # Checks original entire source blob digest and frozen plan before grading.
    rows = read_pinned_source(payload, plan)
    report = grade_rows(rows, observed)
    report["full_upstream_blob_verified"] = True
    return report


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True,
                        help="Exact official GSM8K test.jsonl at the pinned commit")
    parser.add_argument("--observations",
                        default="results/exp012-calibration-observations.json")
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    source = Path(args.source).read_bytes()
    observation_bytes = Path(args.observations).read_bytes()
    observed = json.loads(observation_bytes)
    result = score_pinned_source(source, observed)
    result["raw_observations_sha256"] = hashlib.sha256(observation_bytes).hexdigest()
    result["raw_observations_frozen_commit"] = (
        "6611afa785417c87cc6985929da71f47c645fe61")
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    print("EXP012_EXPLORATORY_CALIBRATION=" + str(result["correct"]) + "/4")


if __name__ == "__main__":
    main()
