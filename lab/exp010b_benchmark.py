"""EXP-010B: deterministic simulated evaluation of EXP-010A routes.

A hand-authored fixture with symbolic answers is not a blind benchmark.
No actual LLM, third-party software, network or scientific discovery.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Mapping

from .exp010a_adaptive import POLICIES, Reply, Task, run

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "experiments" / "exp010b-synthetic-cases.json"
ALPHABET = ("A", "B", "C")
EXPECTED_CASE_IDS = (
    "simple_01", "simple_02", "simple_03", "simple_04",
    "parallel_01", "parallel_02", "parallel_03", "parallel_04",
    "uncertain_01", "uncertain_02", "uncertain_03", "uncertain_04",
    "mandatory_01", "mandatory_02", "limited_01", "limited_02",
)


def validate_fixture(fixture: Mapping) -> None:
    if not isinstance(fixture, dict):
        raise ValueError("Manifest must be an object")
    if (fixture.get("experiment") != "EXP-010B"
            or fixture.get("phase") != "synthetic_architecture_characterization_pre_model"
            or fixture.get("status") != "predeclared_fixtures_not_blind_no_real_model"
            or fixture.get("model_calls") != 0
            or fixture.get("policies") != list(POLICIES)
            or fixture.get("answer_alphabet") != list(ALPHABET)
            or fixture.get("cost_unit") != "abstract_role_invocation_only"):
        raise ValueError("Unexpected EXP-010B preregistration")
    cases = fixture.get("cases")
    if not isinstance(cases, list) or [c.get("id") for c in cases
                                      if isinstance(c, dict)] != list(EXPECTED_CASE_IDS):
        raise ValueError("Missing, extra or reordered cases")
    exact_fields = {
        "id", "uncertainty", "parallelizable", "mandatory_review",
        "budget", "expected", "solver", "independent", "critic_verdict",
    }
    for case in cases:
        if not isinstance(case, dict) or set(case) != exact_fields:
            raise ValueError("Unrecognized fixture fields")
        Task(case["id"], case["uncertainty"], case["parallelizable"],
             case["mandatory_review"], case["budget"])
        if any(case[field] not in ALPHABET for field in
               ("expected", "solver", "independent")):
            raise ValueError("Answers must be symbolic, not untrusted text")
        if case["critic_verdict"] not in ("approve", "reject"):
            raise ValueError("Invalid critic verdict")


def evaluate_case(case: dict, policy: str) -> dict:
    task = Task(case["id"], case["uncertainty"], case["parallelizable"],
                case["mandatory_review"], case["budget"])
    calls = []

    def invoke(profile, role, prior):
        assert profile == task
        if role == "independent" and prior:
            raise AssertionError("Independence violated")
        calls.append(role)
        if role == "critic":
            if len(prior) != 1:
                raise AssertionError("Review must receive exactly one proposal")
            return Reply("synthetic critique", case["critic_verdict"])
        if role == "independent":
            return Reply(case["independent"])
        if role == "solver":
            return Reply(case["solver"])
        raise AssertionError("Unknown role")

    outcome = run(task, invoke, policy)
    if outcome.spent != len(calls) or outcome.spent > task.budget:
        raise AssertionError("Budget or call accounting violated")
    answered = outcome.final is not None
    correct = answered and outcome.final == case["expected"]
    # The ground truth is hand-authored; this verifies mechanics only.
    return {
        "case_id": case["id"],
        "policy": policy,
        "route": outcome.route,
        "status": outcome.status,
        "calls": outcome.spent,
        "answered": answered,
        "correct": correct,
        "incorrect": answered and not correct,
        "blocked": outcome.status == "blocked",
        "abstained": not answered and outcome.status != "blocked",
        "wrong_consensus": outcome.route == "parallel" and answered and not correct,
        "false_critic_approval": outcome.route == "review" and answered and not correct,
        "false_critic_rejection": (
            outcome.route == "review" and outcome.status == "rejected_by_critic"
            and case["solver"] == case["expected"]
        ),
    }


def evaluate(fixture: dict) -> dict:
    validate_fixture(fixture)
    outcomes = [evaluate_case(c, policy) for policy in POLICIES
                for c in fixture["cases"]]
    summary = []
    for policy in POLICIES:
        subset = [o for o in outcomes if o["policy"] == policy]
        counts = Counter({
            "answered": sum(o["answered"] for o in subset),
            "correct": sum(o["correct"] for o in subset),
            "incorrect": sum(o["incorrect"] for o in subset),
            "blocked": sum(o["blocked"] for o in subset),
            "abstained": sum(o["abstained"] for o in subset),
            "role_calls": sum(o["calls"] for o in subset),
            "wrong_consensus": sum(o["wrong_consensus"] for o in subset),
            "false_critic_approval": sum(o["false_critic_approval"] for o in subset),
            "false_critic_rejection": sum(o["false_critic_rejection"] for o in subset),
        })
        if counts["correct"] + counts["incorrect"] + counts["abstained"] + counts["blocked"] != len(subset):
            raise AssertionError("Missing or overlapping outcome statuses")
        summary.append({"policy": policy, "total_cases": len(subset), **dict(counts)})
    return {
        "experiment": "EXP-010B",
        "phase": "mechanical_orchestration_comparison_only",
        "status": "synthetic_hand_authored_not_blind_not_a_model_benchmark",
        "cases": len(fixture["cases"]),
        "policies": len(POLICIES),
        "evaluations": len(outcomes),
        "models_called": 0,
        "real_world_accuracy_measured": False,
        "causal_superiority_claimed": False,
        "budget_unit": "abstract_role_invocation_not_tokens_or_money",
        "summary": summary,
        "per_case": outcomes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/exp010b-synthetic-report.json")
    args = parser.parse_args(argv)
    fixture = json.loads(MANIFEST.read_text(encoding="utf-8"))
    record = evaluate(fixture)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print("EXP010B_SIMULATED_ONLY=" + json.dumps(
        {"cases": record["cases"], "evaluations": record["evaluations"],
         "models": record["models_called"]}, sort_keys=True))


if __name__ == "__main__":
    main()
