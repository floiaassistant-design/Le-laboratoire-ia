"""EXP-011D: guided, offline, *human* collection of real-model trial reports.

This does NOT call any model, open a chat, verify isolation, or score replies.
All session references, model labels and resource metrics are self-reported.
The same pinned EXP-011/011B tasks, order and templates remain unchanged.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
from pathlib import Path
import tempfile

from .exp011_manual import (
    PLAN, load_json, read_pinned_source, verify_prepared_files,
)
from .exp011_provenance import audit
from .exp011_runbook import SOLVER_PLACEHOLDER, make_runbook

MAX_REPLY_BYTES = 1024


def next_step(book: dict, responses: dict, packets: dict) -> dict | None:
    """Get only the next missing role, in the preregistered order.

    Critic sees the *recorded solver output* (not the hidden oracle).
    Independent role never gets the first solver's response.
    """
    report = audit(packets, book, responses)
    if report["duplicated_session_references_count"]:
        raise ValueError("Existing duplicate session references: fix provenance first")
    index = {(x["task_id"], x["policy"]): x for x in responses["records"]}
    for trial in book["trials"]:
        record = index[trial["task_id"], trial["policy"]]
        for step in trial["steps"]:
            role = step["role"]
            if record["outputs"][role] is not None:
                continue
            prompt = step["prompt_template"]
            if role == "critic":
                solver = record["outputs"]["solver"]
                if solver is None:
                    raise ValueError("Critic cannot precede solver")
                # The frozen template already labels this as untrusted solver output.
                # Only the actual self-reported output is inserted, never the key.
                prompt = prompt.replace(SOLVER_PLACEHOLDER, solver.strip())
            if SOLVER_PLACEHOLDER in prompt:
                raise ValueError("Critic template was not resolved")
            return {
                "trial_id": trial["trial_id"],
                "task_id": trial["task_id"], "policy": trial["policy"],
                "split": trial["split"], "route": trial["route"],
                "role": role, "prompt": prompt,
                "fresh_chat_required": True,
                "no_chat_opened_or_model_called": True,
            }
    return None


def record_step(
    packets: dict, book: dict, responses: dict, *,
    task_id: str, policy: str, role: str,
    output: str, session: str, model: str,
    elapsed_seconds: float | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> dict:
    """Return a validated replacement for responses.json; no persistence here.

    Only the next chronological role may be recorded, one time.
    """
    waiting = next_step(book, responses, packets)
    if waiting is None:
        raise ValueError("All scheduled roles are already recorded")
    if (waiting["task_id"], waiting["policy"], waiting["role"]) != (
        task_id, policy, role
    ):
        raise ValueError("Out of order: record the next scheduled role first")
    if not isinstance(output, str) or len(output) > 200:
        raise ValueError("Response text must have at most 200 characters")
    if not isinstance(session, str) or not 1 <= len(session) <= 128:
        raise ValueError("A chat reference of 1..128 characters is required")
    if not isinstance(model, str) or not 1 <= len(model) <= 100:
        raise ValueError("A self-reported model label is required")
    for metric, value in (
        ("elapsed_seconds", elapsed_seconds),
        ("input_tokens", input_tokens),
        ("output_tokens", output_tokens),
    ):
        if value is None:
            continue
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not 0 <= value <= 1_000_000):
            raise ValueError("Invalid " + metric)
        if metric != "elapsed_seconds" and not isinstance(value, int):
            raise ValueError("Token counts must be integers")
    prior_sessions = {
        value for rec in responses["records"]
        for value in rec["sessions"].values() if value is not None
    }
    if session in prior_sessions:
        raise ValueError("This conversation reference was already used")
    labels = {
        rec["model_label"] for rec in responses["records"]
        if rec["model_label"] is not None
    }
    if labels and (labels != {model}):
        raise ValueError("A different model was previously self-reported")
    trial = next(x for x in book["trials"] if x["trial_id"] == waiting["trial_id"])
    is_last_role = role == trial["steps"][-1]["role"]
    if not is_last_role and any(
        x is not None for x in (elapsed_seconds, input_tokens, output_tokens)
    ):
        raise ValueError("Trial-level resource totals may only be recorded with the last role")
    updated = copy.deepcopy(responses)
    rec = next(x for x in updated["records"]
               if x["task_id"] == task_id and x["policy"] == policy)
    if rec["outputs"][role] is not None or rec["sessions"][role] is not None:
        raise ValueError("Refusing to replace an already recorded output")
    rec["outputs"][role] = output
    rec["sessions"][role] = session
    rec["model_label"] = model
    if is_last_role:
        for name, value in (
            ("elapsed_seconds", elapsed_seconds),
            ("input_tokens", input_tokens),
            ("output_tokens", output_tokens),
        ):
            if value is not None:
                rec[name] = value
    audit(packets, book, updated)  # check the entire 64-trial roster before saving
    return updated


def progress(book: dict, responses: dict, packets: dict) -> dict:
    report = audit(packets, book, responses)
    counts = {
        split: {
            "trials": 0, "blocked": 0, "complete_self_reported": 0,
            "partial": 0, "not_started": 0, "roles_reported": 0,
        }
        for split in ("calibration", "evaluation")
    }
    for t in report["trials"]:
        bucket = counts[t["split"]]
        bucket["trials"] += 1
        bucket["roles_reported"] += t["roles_reported"]
        if t["route"] == "blocked":
            bucket["blocked"] += 1
        elif t["roles_reported"] == 0:
            bucket["not_started"] += 1
        elif t["roles_reported"] < t["roles_planned"]:
            bucket["partial"] += 1
        else:
            bucket["complete_self_reported"] += 1
    following = next_step(book, responses, packets)
    return {
        "experiment": "EXP-011D",
        "model_calls_executed_by_guide": 0,
        "model_outputs_self_reported_only": True,
        "session_isolation_verified": False,
        "total_planned_trials": 64,
        "by_split": counts,
        "next": None if following is None else {
            k: following[k] for k in ("trial_id", "role", "split")
        },
    }


def load_study(source: Path, out: Path) -> tuple[dict, dict, dict]:
    """Preflight pinned source and private key in memory; never return the key."""
    rows = read_pinned_source(source.read_bytes(), load_json(PLAN))
    packets = load_json(out / "questions.json")
    key = load_json(out / "ANSWER-KEY-PRIVATE.json")
    verify_prepared_files(rows, load_json(PLAN), packets, key)
    book = load_json(out / "manual-runbook.json")
    if book != make_runbook(packets):
        raise ValueError("The runbook was modified")
    responses = load_json(out / "responses.json")
    audit(packets, book, responses)
    return packets, book, responses


def atomic_write(path: Path, data: dict) -> None:
    """Replace the private response file atomically, never via partial JSON."""
    if not path.is_file():
        raise ValueError("Expected an existing responses.json")
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(path.parent),
            prefix=".exp011d-", suffix=".tmp", delete=False
        ) as stream:
            tmp = Path(stream.name)
            os.chmod(tmp, 0o600)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if tmp is not None and tmp.exists():
            tmp.unlink()


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="Pinned original GSM8K test.jsonl (offline)")
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="Previously prepared private EXP-011 directory")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("next", help="Print only the next prompt; no chat is opened")
    commands.add_parser("status", help="Show private recording progress, not answers")
    record = commands.add_parser("record", help="Save one manually copied model output")
    record.add_argument("--task-id", required=True)
    record.add_argument("--policy", required=True)
    record.add_argument("--role", required=True, choices=("solver", "independent", "critic"))
    record.add_argument("--response-file", type=Path, required=True,
                        help="UTF-8 file with actual model response; never the oracle")
    record.add_argument("--session", required=True,
                        help="Reference of an actual separate chat (self-reported)")
    record.add_argument("--model", required=True, help="Actual model label, self-reported")
    record.add_argument("--elapsed-seconds", type=float)
    record.add_argument("--input-tokens", type=int)
    record.add_argument("--output-tokens", type=int)
    args = parser.parse_args(argv)
    packets, book, responses = load_study(args.source, args.out_dir)
    if args.command == "next":
        step = next_step(book, responses, packets)
        if step is None:
            print("All recorded; score and audit separately after verification")
        else:
            print("TRIAL " + step["trial_id"] + " | role " + step["role"])
            print("OPEN A NEW CHAT MANUALLY. MODEL AND ISOLATION NOT VERIFIED.")
            print("\n" + step["prompt"] + "\n")
    elif args.command == "status":
        print(json.dumps(progress(book, responses, packets), indent=2))
    else:
        data = args.response_file.read_bytes()
        if len(data) > MAX_REPLY_BYTES:
            raise ValueError("Response file is too large")
        reply = data.decode("utf-8").strip()
        updated = record_step(
            packets, book, responses, task_id=args.task_id,
            policy=args.policy, role=args.role, output=reply,
            session=args.session, model=args.model,
            elapsed_seconds=args.elapsed_seconds,
            input_tokens=args.input_tokens, output_tokens=args.output_tokens,
        )
        atomic_write(args.out_dir / "responses.json", updated)
        print("Saved one self-reported role; no model called and no scoring done")


if __name__ == "__main__":
    main()
