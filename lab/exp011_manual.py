"""EXP-011: offline, human-run protocol for genuine public GSM8K tasks.

This module NEVER calls an LLM or network service. It emits question-only
packets plus a separate key, then evaluates manually recorded final answers.
An empty response template is not a model evaluation.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re

from .exp010a_adaptive import Task, Reply, POLICIES, choose, run

ROOT = Path(__file__).resolve().parent.parent
PLAN = ROOT / "experiments" / "exp011-gsm8k-plan.json"
SOURCE_COMMIT = "3101c7d5072418e28b9008a6636bde82a006892c"
SOURCE_BLOB = "e4c2ff4942b9a78bd74f04141224c11e28d12dc9"
SOURCE_PATH = "grade_school_math/data/test.jsonl"
NUMBER = r"-?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?"
FINAL = re.compile(r"FINAL:\s*(" + NUMBER + r")\s*\Z")
GOLD = re.compile(r"####\s*(" + NUMBER + r")\s*\Z")
CRITIC = re.compile(r"VERDICT:\s*(APPROVE|REJECT)\s*\Z")
ROLES = ("solver", "independent", "critic")
MAX_SOURCE_BYTES = 1_500_000
CALIBRATION = (13, 37, 59, 81)
EVALUATION = (103, 158, 202, 271, 349, 418, 503, 611, 704, 826, 943, 1159)


def validate_plan(plan: dict) -> None:
    if not isinstance(plan, dict):
        raise ValueError("Missing plan")
    src = plan.get("dataset", {})
    if (plan.get("experiment") != "EXP-011"
            or plan.get("phase") != "preregistered_real_task_manual_model_protocol"
            or plan.get("status") != "prepared_no_model_execution_no_measured_outcomes"
            or plan.get("policies") != list(POLICIES)
            or plan.get("model_executions") != 0
            or plan.get("results_committed") != 0
            or plan.get("selected_before_outcomes") is not True
            or plan.get("indices_base") != 0
            or plan.get("calibration_indices") != list(CALIBRATION)
            or plan.get("evaluation_indices") != list(EVALUATION)
            or src.get("upstream_repo") != "openai/grade-school-math"
            or src.get("revision") != SOURCE_COMMIT
            or src.get("relative_path") != SOURCE_PATH
            or src.get("git_blob_sha") != SOURCE_BLOB
            or src.get("source_lines") != 1319
            or src.get("license") != "MIT"):
        raise ValueError("EXP-011 pre-registration changed")
    routing = plan.get("routing_rule", {})
    if (routing.get("feature") != "question_word_count_only"
            or routing.get("uncertainty_ge_50_words") != 2
            or routing.get("uncertainty_below_50_words") != 0
            or routing.get("parallelizable_ge_40_words") is not True
            or routing.get("parallelizable_below_40_words") is not False
            or routing.get("mandatory_review") is not False
            or routing.get("budget_per_case") != 2
            or routing.get("routing_is_not_learned") is not True):
        raise ValueError("Routing rule changed")
    if set(CALIBRATION) & set(EVALUATION):
        raise ValueError("Calibration overlaps validation")
    if plan.get("benchmark_limits", {}).get("independent_holdout_claim") is not False:
        raise ValueError("No independent holdout claim permitted")


def git_blob_sha(payload: bytes) -> str:
    envelope = b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
    return hashlib.sha1(envelope).hexdigest()


def normalized_number(source: str, *, expected: bool = False) -> str:
    regex = GOLD if expected else FINAL
    match = regex.fullmatch(source.strip())
    if not match:
        raise ValueError("Invalid strict numeric answer")
    try:
        number = Decimal(match.group(1).replace(",", ""))
    except InvalidOperation:
        raise ValueError("Invalid numeric data") from None
    if not number.is_finite() or len(number.as_tuple().digits) > 64:
        raise ValueError("Invalid numeric magnitude")
    return str(number.normalize())


def read_pinned_source(payload: bytes, plan: dict) -> list:
    validate_plan(plan)
    if not isinstance(payload, bytes) or len(payload) > MAX_SOURCE_BYTES:
        raise ValueError("Invalid upstream byte payload")
    if git_blob_sha(payload) != SOURCE_BLOB:
        raise ValueError("Source blob is not the pre-registered dataset")
    text = payload.decode("utf-8")
    lines = text.splitlines()
    if len(lines) != 1319:
        raise ValueError("Unexpected upstream test-row count")
    rows = []
    for line in lines:
        obj = json.loads(line)
        if not isinstance(obj, dict) or not isinstance(obj.get("question"), str):
            raise ValueError("Corrupt question data")
        if not isinstance(obj.get("answer"), str):
            raise ValueError("Corrupt key data")
        rows.append(obj)
    return rows


def task_profile(question: str, identity: str) -> Task:
    words = len(question.split())
    # Predeclared input-only rule; it does not inspect solutions.
    return Task(identity, 2 if words >= 50 else 0,
                words >= 40, False, 2)


def make_packet_data(rows: list, plan: dict, plan_sha256: str) -> tuple:
    validate_plan(plan)
    if len(rows) != 1319:
        raise ValueError("Cannot silently change the cohort")
    tasks = []
    answer_key = {}
    template = []
    for split, indices in (("calibration", CALIBRATION), ("evaluation", EVALUATION)):
        for index in indices:
            item = rows[index]
            question = item["question"]
            if not 1 <= len(question) <= 6000 or "####" in question:
                raise ValueError("Invalid or contaminated question")
            identity = "gsm8k-test-" + str(index).zfill(4)
            task = task_profile(question, identity)
            answer_key[identity] = normalized_number(item["answer"].splitlines()[-1], expected=True)
            tasks.append({
                "task_id": identity, "split": split, "row_index": index,
                "question": question,
                "input_word_count": len(question.split()),
                "uncertainty": task.uncertainty,
                "parallelizable": task.parallelizable,
                "mandatory_review": task.mandatory_review,
                "budget": task.budget,
                "routes": {p: choose(task, p) for p in POLICIES},
            })
            for policy in POLICIES:
                template.append({
                    "task_id": identity, "policy": policy,
                    "model_label": None,
                    "outputs": {r: None for r in ROLES},
                    "sessions": {r: None for r in ROLES},
                    "elapsed_seconds": None, "input_tokens": None,
                    "output_tokens": None,
                })
    packets = {
        "experiment": "EXP-011", "kind": "question_only_packets",
        "plan_sha256": plan_sha256, "source_blob_sha": SOURCE_BLOB,
        "model_answers_included": False,
        "tasks": tasks,
        "role_instructions": {
            "solver": "New chat; solve the QUESTION independently. Respond ONLY: FINAL: <number>. Do not use external tools.",
            "independent": "Fresh separate chat; do not see solver's output. Respond ONLY: FINAL: <number>. No tools.",
            "critic": "Fresh chat; see QUESTION and solver FINAL only. Decide whether to approve that final numeric answer. Respond ONLY: VERDICT: APPROVE or VERDICT: REJECT. No tools.",
        },
    }
    key = {"experiment": "EXP-011", "kind": "private_local_answer_key",
           "plan_sha256": plan_sha256, "source_blob_sha": SOURCE_BLOB,
           "answers": answer_key}
    records = {"experiment": "EXP-011", "kind": "self_reported_manual_record_template",
               "plan_sha256": plan_sha256, "records": template}
    return packets, key, records


def verify_prepared_files(rows: list, plan: dict, packets: dict, key: dict) -> None:
    """Enforce that scored questions and key still match the pinned source."""
    plan_sha = hashlib.sha256(PLAN.read_bytes()).hexdigest()
    expected_pack, expected_key, _ = make_packet_data(rows, plan, plan_sha)
    if packets != expected_pack or key != expected_key:
        raise ValueError("Manual study packet or gold key differs from pinned corpus")


def _optional_metric(record, name, *, integral=False):
    value = record[name]
    if value is None:
        return None
    if isinstance(value, bool) or (integral and not isinstance(value, int)):
        raise ValueError("Invalid metric")
    if not isinstance(value, (int, float)) or not 0 <= value <= 1_000_000:
        raise ValueError("Invalid metric")
    return value


def score(packets: dict, key: dict, responses: dict) -> dict:
    if (packets.get("kind") != "question_only_packets"
            or packets.get("model_answers_included") is not False
            or key.get("kind") != "private_local_answer_key"
            or responses.get("kind") != "self_reported_manual_record_template"
            or any(x.get("experiment") != "EXP-011" for x in (packets, key, responses))
            or len({x.get("plan_sha256") for x in (packets, key, responses)}) != 1
            or key.get("source_blob_sha") != packets.get("source_blob_sha")):
        raise ValueError("Unmatched or untrusted manual evaluation files")
    plan_sha = hashlib.sha256(PLAN.read_bytes()).hexdigest()
    if packets.get("plan_sha256") != plan_sha or packets.get("source_blob_sha") != SOURCE_BLOB:
        raise ValueError("Unregistered source or plan fingerprint")
    tasks = packets["tasks"]
    if (len(tasks) != 16 or [t["row_index"] for t in tasks]
            != list(CALIBRATION) + list(EVALUATION)):
        raise ValueError("Unregistered task set")
    expected_ids = [t["task_id"] for t in tasks]
    if set(key["answers"]) != set(expected_ids):
        raise ValueError("Key does not cover exact cohort")
    records = responses["records"]
    if not isinstance(records, list) or len(records) != 16 * len(POLICIES):
        raise ValueError("Incomplete response roster")
    index = {}
    expected_pairs = {(id_, policy) for id_ in expected_ids for policy in POLICIES}
    expected_keys = {"task_id", "policy", "model_label", "outputs", "sessions",
                     "elapsed_seconds", "input_tokens", "output_tokens"}
    for rec in records:
        if not isinstance(rec, dict) or set(rec) != expected_keys:
            raise ValueError("Malformed response record")
        pair = rec["task_id"], rec["policy"]
        if pair in index or pair not in expected_pairs:
            raise ValueError("Duplicate or alien response record")
        if (not isinstance(rec["outputs"], dict) or set(rec["outputs"]) != set(ROLES)
                or not isinstance(rec["sessions"], dict)
                or set(rec["sessions"]) != set(ROLES)):
            raise ValueError("Malformed role data")
        if rec["model_label"] is not None and (not isinstance(rec["model_label"], str)
                or not 1 <= len(rec["model_label"]) <= 100):
            raise ValueError("Invalid model label")
        for metric in ("elapsed_seconds", "input_tokens", "output_tokens"):
            _optional_metric(rec, metric, integral=metric != "elapsed_seconds")
        for role in ROLES:
            output, sess = rec["outputs"][role], rec["sessions"][role]
            if output is not None and (not isinstance(output, str) or len(output) > 200):
                raise ValueError("Invalid role output")
            if sess is not None and (not isinstance(sess, str) or not 1 <= len(sess) <= 128):
                raise ValueError("Invalid session reference")
            if (output is None) != (sess is None):
                raise ValueError("A response and a session must be reported together")
        index[pair] = rec
    if set(index) != expected_pairs:
        raise ValueError("Response roster has missing cases")

    outcomes = []
    labels = set()
    for t in tasks:
        if (t["task_id"] != "gsm8k-test-" + str(t["row_index"]).zfill(4)
                or t["split"] != ("calibration" if t["row_index"] in CALIBRATION else "evaluation")
                or not isinstance(t.get("question"), str)
                or t.get("input_word_count") != len(t["question"].split())):
            raise ValueError("Task identity or question metadata changed")
        profile = task_profile(t["question"], t["task_id"])
        if (profile.uncertainty != t["uncertainty"]
                or profile.parallelizable != t["parallelizable"]
                or profile.mandatory_review != t["mandatory_review"]
                or profile.budget != t["budget"]):
            raise ValueError("Input-only routing profile was manipulated")
        if {p: choose(profile, p) for p in POLICIES} != t["routes"]:
            raise ValueError("Task routes were manipulated")
        for policy in POLICIES:
            rec = index[(t["task_id"], policy)]
            route = choose(profile, policy)
            required = (() if route == "blocked" else
                        ("solver",) if route == "single" else
                        ("solver", "independent") if route == "parallel" else
                        ("solver", "critic"))
            unexpected = set(ROLES) - set(required)
            if any(rec["outputs"][r] is not None for r in unexpected):
                raise ValueError("Unselected roles must not be invoked")
            logged = sum(rec["outputs"][r] is not None for r in required)
            if route == "blocked":
                status, answer = "blocked_by_design", None
            elif logged != len(required):
                status, answer = "unobserved_or_incomplete", None
            elif not rec["model_label"]:
                status, answer = "missing_model_provenance", None
            elif len({rec["sessions"][r] for r in required}) != len(required):
                status, answer = "nonindependent_sessions", None
            else:
                labels.add(rec["model_label"])
                try:
                    answers = {r: normalized_number(rec["outputs"][r])
                               for r in required if r != "critic"}
                    if "critic" in required and not CRITIC.fullmatch(rec["outputs"]["critic"].strip()):
                        raise ValueError("Malformed critic vote")
                    vote = (CRITIC.fullmatch(rec["outputs"]["critic"].strip()).group(1).lower()
                            if "critic" in required else None)

                    def callback(_task, role, prior):
                        if role == "critic":
                            return Reply("manual critic vote", vote)
                        return Reply(answers[role])

                    result = run(profile, callback, policy)
                    answer = result.final
                    if answer is None:
                        status = "abstained"
                    elif Decimal(answer) == Decimal(key["answers"][t["task_id"]]):
                        status = "correct"
                    else:
                        status = "incorrect"
                except (ValueError, InvalidOperation):
                    status, answer = "malformed_response", None
            outcomes.append({
                "task_id": t["task_id"], "split": t["split"], "policy": policy,
                "route": route, "status": status,
                "role_calls_self_reported": logged,
                "elapsed_seconds_self_reported": rec["elapsed_seconds"],
                "input_tokens_self_reported": rec["input_tokens"],
                "output_tokens_self_reported": rec["output_tokens"],
            })

    summaries = []
    for split in ("calibration", "evaluation"):
        for policy in POLICIES:
            subset = [r for r in outcomes if r["split"] == split and r["policy"] == policy]
            statuses = {status: sum(r["status"] == status for r in subset)
                        for status in ("correct", "incorrect", "abstained",
                                       "blocked_by_design", "unobserved_or_incomplete",
                                       "missing_model_provenance", "nonindependent_sessions",
                                       "malformed_response")}
            attempted = sum(statuses[s] for s in ("correct", "incorrect", "abstained"))
            known = [r for r in subset if r["status"] in ("correct", "incorrect", "abstained")]
            summaries.append({
                "split": split, "policy": policy, "tasks_total": len(subset),
                "observed_complete": attempted, "correct": statuses["correct"],
                "observed_accuracy": (
                    statuses["correct"] / attempted if attempted else None),
                "role_calls_self_reported": sum(r["role_calls_self_reported"] for r in subset),
                "elapsed_seconds_total": (
                    sum(r["elapsed_seconds_self_reported"] for r in known)
                    if known and all(r["elapsed_seconds_self_reported"] is not None
                                     for r in known) else None),
                "statuses": statuses,
            })
    return {
        "experiment": "EXP-011", "phase": "manual_trials_only",
        "model_execution_proof": "not_verifiable_from_self_reported_logs",
        "real_model_results_recorded": sum(
            r["status"] in ("correct", "incorrect", "abstained") for r in outcomes),
        "model_labels_self_reported": sorted(labels),
        "mixed_model_label_warning": len(labels) > 1,
        "public_benchmark_training_contamination_possible": True,
        "independent_holdout_claim": False,
        "evaluations": outcomes, "summary": summaries,
    }


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
                    + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    preflight = commands.add_parser("preflight")
    preflight.add_argument("--output", default="results/exp011-protocol-preflight.json")
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--source", required=True, help="Pinned upstream test.jsonl file")
    prepare.add_argument("--out-dir", required=True)
    grading = commands.add_parser("score")
    grading.add_argument("--source", required=True, help="Same pinned upstream test.jsonl file")
    grading.add_argument("--out-dir", required=True)
    grading.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    if args.command == "preflight":
        plan_raw = PLAN.read_bytes()
        plan = json.loads(plan_raw)
        validate_plan(plan)
        save_json(Path(args.output), {
            "experiment": "EXP-011",
            "phase": "preregistration_offline_validation_only",
            "source_revision": SOURCE_COMMIT,
            "source_blob_sha": SOURCE_BLOB,
            "plan_sha256": hashlib.sha256(plan_raw).hexdigest(),
            "calibration_tasks_selected": len(CALIBRATION),
            "evaluation_tasks_selected": len(EVALUATION),
            "policies": list(POLICIES),
            "model_calls": 0,
            "model_scores": 0,
            "upstream_dataset_downloaded": False,
            "real_model_evaluation_performed": False,
        })
        print("EXP011_PREFLIGHT_NO_MODEL_RUNS=16 tasks preregistered")
    elif args.command == "prepare":
        plan_raw = PLAN.read_bytes()
        plan = json.loads(plan_raw)
        validate_plan(plan)
        rows = read_pinned_source(Path(args.source).read_bytes(), plan)
        pack, key, response = make_packet_data(
            rows, plan, hashlib.sha256(plan_raw).hexdigest())
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        if any((out / name).exists() for name in (
                "questions.json", "ANSWER-KEY-PRIVATE.json", "responses.json")):
            raise ValueError("Refusing to overwrite existing experiment files")
        save_json(out / "questions.json", pack)
        save_json(out / "ANSWER-KEY-PRIVATE.json", key)
        save_json(out / "responses.json", response)
        print("EXP011_PREPARED_NO_MODEL_CALLS=16 tasks; separate local key")
    else:
        out = Path(args.out_dir)
        plan = load_json(PLAN)
        rows = read_pinned_source(Path(args.source).read_bytes(), plan)
        packets = load_json(out / "questions.json")
        key = load_json(out / "ANSWER-KEY-PRIVATE.json")
        verify_prepared_files(rows, plan, packets, key)
        report = score(packets, key, load_json(out / "responses.json"))
        save_json(Path(args.report), report)
        print("EXP011_RECORDED_OBSERVATIONS=" + str(report["real_model_results_recorded"]))


if __name__ == "__main__":
    main()
