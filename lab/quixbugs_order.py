"""EXP-005: effect of the ORDER of existing targeted probes, not new probes.

The 12 test inputs per QuixBugs program come unchanged from EXP-004B.
All candidate outputs are evaluated once in a child process; the permutations
are simulated from those fixed observations. This is an EXPLORATORY analysis.
No LLM, API or additional input-generation methods are involved.
"""
from __future__ import annotations

import argparse
from itertools import chain
import json
from math import comb
from pathlib import Path
from random import Random
import subprocess
import sys

from .quixbugs_external import PROGRAMS, BUDGETS, edge_probes
from .quixbugs_screen import ROOT, invoke, load_function

SEED = 20261103
PERMUTATIONS = 256
CALL_TIMEOUT_SECONDS = 0.03
CHILD_TIMEOUT_SECONDS = 20
TOTAL_PROBES = 12


def probability_hit(detecting_inputs: int, budget: int, total: int = TOTAL_PROBES) -> float:
    """Exact probability a uniform random permutation hits any exposing input."""
    if not 0 <= detecting_inputs <= total or not 0 <= budget <= total:
        raise ValueError("Invalid count or budget")
    if budget == 0 or detecting_inputs == 0:
        return 0.0
    if total - detecting_inputs < budget:
        return 1.0
    return 1.0 - comb(total - detecting_inputs, budget) / comb(total, budget)


def prefix_hits(outcomes: tuple[bool, ...] | list[bool], order: list[int],
                budget: int) -> bool:
    if sorted(order) != list(range(len(outcomes))):
        raise ValueError("Order must be a permutation of the original tests")
    if not 0 <= budget <= len(outcomes):
        raise ValueError("Invalid budget")
    return any(outcomes[index] for index in order[:budget])


def permutation_orders(index: int, repeats: int = PERMUTATIONS) -> list[list[int]]:
    """Uniform shuffle with stable seed for each program and repetition."""
    if not 0 <= index < len(PROGRAMS) or repeats <= 0:
        raise ValueError("Invalid program index or repetitions")
    all_orders = []
    for repeat in range(repeats):
        order = list(range(TOTAL_PROBES))
        Random(SEED + index * 100_003 + repeat * 1_009).shuffle(order)
        all_orders.append(order)
    return all_orders


def evaluate_program(name: str) -> dict:
    """One subprocess per program; no score-guided selection of probes."""
    if name not in PROGRAMS:
        raise ValueError("Unknown program")
    fixed, buggy = load_function("correct", name), load_function("buggy", name)
    rows = []
    for ordinal, args in enumerate(edge_probes(name)):
        reference = invoke(fixed, list(args), CALL_TIMEOUT_SECONDS)
        if reference["status"] != "ok":
            rows.append({"index": ordinal, "oracle_valid": False,
                         "oracle_status": reference["status"],
                         "bug_detected": False, "bug_status": None})
            continue
        candidate = invoke(buggy, list(args), CALL_TIMEOUT_SECONDS)
        detected = (candidate["status"] != "ok"
                    or candidate["value"] != reference["value"])
        rows.append({"index": ordinal, "oracle_valid": True,
                     "oracle_status": "ok", "bug_detected": detected,
                     "bug_status": candidate["status"]})
    assert len(rows) == TOTAL_PROBES
    return {"program": name, "input_checks": rows,
            "oracle_invalid": sum(not x["oracle_valid"] for x in rows),
            "detecting_inputs": sum(x["bug_detected"] for x in rows)}


def _load_outcomes() -> tuple[list[dict], list[dict]]:
    details = []
    failures = []
    for name in PROGRAMS:
        try:
            worker = subprocess.run(
                [sys.executable, "-m", "lab.quixbugs_order", "--child", name],
                capture_output=True, text=True, timeout=CHILD_TIMEOUT_SECONDS,
                cwd=ROOT, check=False)
            if worker.returncode:
                failures.append({"program": name, "reason": "worker_error",
                                 "returncode": worker.returncode,
                                 "stderr_tail": worker.stderr[-300:]})
            else:
                details.append(json.loads(worker.stdout))
        except subprocess.TimeoutExpired:
            failures.append({"program": name, "reason": "worker_timeout"})
        except (json.JSONDecodeError, OSError) as exc:
            failures.append({"program": name, "reason": type(exc).__name__})
    return details, failures


def analyze(outcomes_by_program: list[dict], repeats: int = PERMUTATIONS) -> dict:
    if len(outcomes_by_program) != len(PROGRAMS):
        raise ValueError("All 16 programs must be present")
    table = {d["program"]: d for d in outcomes_by_program}
    if set(table) != set(PROGRAMS):
        raise ValueError("Duplicate or missing programs")
    if repeats < 1:
        raise ValueError("Invalid permutation count")

    program_rows = []
    across = {b: [0] * repeats for b in BUDGETS}
    baseline = {b: 0 for b in BUDGETS}
    expected = {b: 0.0 for b in BUDGETS}
    variance = {b: 0.0 for b in BUDGETS}

    for idx, name in enumerate(PROGRAMS):
        data = table[name]
        outcomes = [x["bug_detected"] for x in data["input_checks"]]
        if len(outcomes) != TOTAL_PROBES:
            raise ValueError(f"Incorrect input budget for {name}")
        count = sum(outcomes)
        orders = permutation_orders(idx, repeats)
        per_budget = {}
        for budget in BUDGETS:
            original = prefix_hits(outcomes, list(range(TOTAL_PROBES)), budget)
            hits = [int(prefix_hits(outcomes, order, budget)) for order in orders]
            exact = probability_hit(count, budget)
            baseline[budget] += int(original)
            expected[budget] += exact
            variance[budget] += exact * (1.0 - exact)
            across[budget] = [a + b for a, b in zip(across[budget], hits)]
            per_budget[str(budget)] = {
                "original_detected": original,
                "random_order_hits": sum(hits),
                "random_order_trials": repeats,
                "exact_probability": round(exact, 9)}
        program_rows.append({
            "program": name, "detecting_inputs": count,
            "oracle_invalid": data["oracle_invalid"],
            "per_budget": per_budget,
            "input_checks": data["input_checks"]})

    summary = []
    for budget in BUDGETS:
        dist = sorted(across[budget])
        summary.append({
            "budget": budget,
            "fixed_order_detected_programs": baseline[budget],
            "expected_random_order_detected_programs": round(expected[budget], 6),
            "random_order_sd_programs": round(variance[budget] ** .5, 6),
            "sampled_mean_detected_programs": round(sum(dist) / repeats, 6),
            "sampled_min_detected_programs": dist[0],
            "sampled_max_detected_programs": dist[-1],
            "sampled_p10_detected_programs": dist[int((repeats - 1) * .10)],
            "sampled_p90_detected_programs": dist[int((repeats - 1) * .90)],
            "theoretical_max_detectable_programs": sum(
                x["detecting_inputs"] > 0 for x in program_rows)
        })
    return {
        "experiment": "EXP-005", "scope": "Exploratory permutation ablation on known QuixBugs cases; NOT a holdout and NOT agents",
        "source_commit": "4257f44b0ff1181dedaedee6a447e133219fcebf",
        "seed": SEED, "permutations_per_program": repeats,
        "budgets": list(BUDGETS), "programs": list(PROGRAMS),
        "total_probes_per_program": TOTAL_PROBES,
        "oracle_invalid_inputs": sum(x["oracle_invalid"] for x in program_rows),
        "summary": summary, "program_details": program_rows,
    }


def run() -> dict:
    details, failures = _load_outcomes()
    if failures:
        raise RuntimeError(f"Cannot calculate partial outcome set: {failures}")
    return analyze(details)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", choices=PROGRAMS)
    parser.add_argument("--output", default="results/exp005.json")
    args = parser.parse_args(argv)
    if args.child:
        print(json.dumps(evaluate_program(args.child), ensure_ascii=False))
        return
    result = run()
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("EXP005_SUMMARY=" + json.dumps({
        "program_count": len(result["programs"]),
        "oracle_invalid_inputs": result["oracle_invalid_inputs"],
        "summary": result["summary"],
        "detecting_inputs_by_program": {
            x["program"]: x["detecting_inputs"]
            for x in result["program_details"]}
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
