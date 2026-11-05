"""EXP-011B: balanced, question-only manual trial runbook.

The runbook schedules *human-operated* ChatGPT trials. It neither calls a
model nor creates isolated conversations. No gold answers enter prompts.
The EXP-011 preregistered corpus, four policies and routing rule stay frozen.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .exp010a_adaptive import POLICIES, choose
from .exp011_manual import (
    CALIBRATION, EVALUATION, PLAN, SOURCE_BLOB, load_json,
    read_pinned_source, task_profile, verify_prepared_files,
)

MODEL_CALLS = 0
SOLVER_PLACEHOLDER = "{{SOLVER_FINAL}}"


def _role_prompt(role: str, question: str) -> str:
    base = "QUESTION:\n" + question
    if role == "solver":
        return ("Fresh chat; solve independently, without external tools. "
                "Reply ONLY with FINAL: <number>.\n\n" + base)
    if role == "independent":
        return ("A NEW separate chat; independently solve without seeing the "
                "first solver's answer. No external tools. "
                "Reply ONLY with FINAL: <number>.\n\n" + base)
    if role == "critic":
        return ("A NEW separate chat; evaluate the proposed numeric final "
                "answer to the question below. You are not shown an oracle. "
                "No external tools. Reply ONLY with VERDICT: APPROVE or "
                "VERDICT: REJECT.\n\n" + base + "\n\n"
                "SOLVER FINAL (paste the solver's exact output here):\n"
                + SOLVER_PLACEHOLDER)
    raise ValueError("Unexpected role")


def _roles(route: str) -> tuple[str, ...]:
    return {
        "blocked": (),
        "single": ("solver",),
        "parallel": ("solver", "independent"),
        "review": ("solver", "critic"),
    }[route]


def make_runbook(packets: dict) -> dict:
    """Create a deterministic balanced schedule from question-only packets.

    All routes, question counts and source/plan fingerprints are checked.
    The CLI also validates packet AND private key against the pinned source
    before calling this function. Actual isolation remains operator-reported.
    """
    plan_sha = hashlib.sha256(PLAN.read_bytes()).hexdigest()
    if (not isinstance(packets, dict)
            or packets.get("experiment") != "EXP-011"
            or packets.get("kind") != "question_only_packets"
            or packets.get("model_answers_included") is not False
            or packets.get("source_blob_sha") != SOURCE_BLOB
            or packets.get("plan_sha256") != plan_sha):
        raise ValueError("Untrusted question-only packet")
    tasks = packets.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 16:
        raise ValueError("Incomplete question-only roster")
    expected_indices = list(CALIBRATION) + list(EVALUATION)
    if [t.get("row_index") for t in tasks if isinstance(t, dict)] != expected_indices:
        raise ValueError("Unexpected task order or indices")

    schedule = []
    positions = {"calibration": Counter(), "evaluation": Counter()}
    for split, indices in (("calibration", CALIBRATION),
                           ("evaluation", EVALUATION)):
        selection = [t for t in tasks if t["split"] == split]
        if len(selection) != len(indices):
            raise ValueError("Unexpected split")
        for ordinal, task in enumerate(selection):
            question = task.get("question")
            task_id = "gsm8k-test-" + str(indices[ordinal]).zfill(4)
            if (task.get("task_id") != task_id or
                    not isinstance(question, str) or
                    not 1 <= len(question) <= 6000 or
                    "####" in question or
                    task.get("input_word_count") != len(question.split())):
                raise ValueError("Untrusted task or question")
            profile = task_profile(question, task_id)
            if (task.get("uncertainty") != profile.uncertainty or
                    task.get("parallelizable") != profile.parallelizable or
                    task.get("mandatory_review") != profile.mandatory_review or
                    task.get("budget") != profile.budget or
                    task.get("routes") != {p: choose(profile, p) for p in POLICIES}):
                raise ValueError("Route differs from the frozen EXP-011 policy")
            # Each of four policies occurs equally often at positions 1..4
            # in both splits (4 calibration tasks, 12 evaluation tasks).
            rotated = tuple(POLICIES[(ordinal + position) % 4]
                            for position in range(4))
            for position, policy in enumerate(rotated, start=1):
                positions[split][(position, policy)] += 1
                route = choose(profile, policy)
                steps = []
                for role in _roles(route):
                    steps.append({
                        "role": role,
                        "planned_context_slot": task_id + ":" + policy + ":" + role,
                        "requires_fresh_chat": True,
                        "prompt_template": _role_prompt(role, question),
                    })
                schedule.append({
                    "trial_id": task_id + ":" + policy,
                    "task_id": task_id,
                    "split": split,
                    "task_position": ordinal + 1,
                    "policy_position": position,
                    "policy": policy,
                    "route": route,
                    "role_calls_planned": len(steps),
                    "steps": steps,
                })
    counts = {}
    for split, indices in (("calibration", CALIBRATION), ("evaluation", EVALUATION)):
        expected_per_position = len(indices) // len(POLICIES)
        if any(positions[split][(pos, p)] != expected_per_position
               for pos in range(1, 5) for p in POLICIES):
            raise AssertionError("Policy order imbalance")
        counts[split] = {
            str(pos): {p: positions[split][(pos, p)] for p in POLICIES}
            for pos in range(1, 5)
        }
    return {
        "experiment": "EXP-011B",
        "phase": "manual_runbook_only_no_model_execution",
        "source_experiment": "EXP-011",
        "source_blob_sha": SOURCE_BLOB,
        "plan_sha256": plan_sha,
        "model_calls_executed": MODEL_CALLS,
        "no_real_model_evaluation": True,
        "sessions_independent_verified": False,
        "gold_answers_included": False,
        "total_trials_planned": len(schedule),
        "role_calls_planned": sum(x["role_calls_planned"] for x in schedule),
        "policy_order_counts": counts,
        "instructions": (
            "Perform calibration before evaluation. Follow trial order. "
            "Each planned context slot requires a genuinely new chat; "
            "fill actual session references in responses.json. "
            "The critic template requires manually pasting ONLY the "
            "solver FINAL, never the hidden answer key. "
            "No automatic model execution, isolation or cost measurement."),
        "trials": schedule,
    }


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True,
                        help="Pinned official GSM8K test.jsonl")
    parser.add_argument("--out-dir", required=True,
                        help="Local private EXP-011 study directory")
    args = parser.parse_args(argv)
    out = Path(args.out_dir)
    rows = read_pinned_source(Path(args.source).read_bytes(), load_json(PLAN))
    pack = load_json(out / "questions.json")
    key = load_json(out / "ANSWER-KEY-PRIVATE.json")
    verify_prepared_files(rows, load_json(PLAN), pack, key)
    runbook = make_runbook(pack)
    destination = out / "manual-runbook.json"
    if destination.exists():
        raise ValueError("Refusing to overwrite an existing manual runbook")
    destination.write_text(json.dumps(runbook, ensure_ascii=False,
                                      indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("EXP011B_RUNBOOK_ONLY=" + str(runbook["total_trials_planned"]) +
          " planned trials; zero model calls")


if __name__ == "__main__":
    main()
