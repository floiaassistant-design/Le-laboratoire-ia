"""EXP-006A: input-only diversity ordering on the *four* QuixBugs pilots.

QuixBugs buggy versions are read only AFTER constructing the order.
No 16-program holdout evaluation; no model, API or paid service.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from .priority import prioritize, prioritization_cost
from .quixbugs_pilot import PILOT, BUDGETS, domain_probes
from .quixbugs_order import probability_hit
from .quixbugs_screen import ROOT, load_function, invoke

CALL_TIMEOUT_SECONDS = 0.03
WORKER_TIMEOUT_SECONDS = 15


def evaluate_program(name: str) -> dict:
    if name not in PILOT:
        raise ValueError("Only four predeclared pilot programs permitted")
    probes = domain_probes(name)
    # Freeze order based ONLY on input values, before loading faulty code.
    proposed_order = prioritize(probes)
    assert len(proposed_order) == len(probes) == 12

    reference, buggy = load_function("correct", name), load_function("buggy", name)
    outcomes = []
    for index, args in enumerate(probes):
        oracle = invoke(reference, list(args), CALL_TIMEOUT_SECONDS)
        if oracle["status"] != "ok":
            outcomes.append({"index": index, "oracle_valid": False,
                             "detected": False, "oracle_status": oracle["status"]})
            continue
        candidate = invoke(buggy, list(args), CALL_TIMEOUT_SECONDS)
        outcomes.append({"index": index, "oracle_valid": True,
                         "detected": candidate["status"] != "ok"
                             or candidate["value"] != oracle["value"],
                         "bug_status": candidate["status"]})
    return {"program": name, "priority_indices": proposed_order,
            "oracle_invalid": sum(not r["oracle_valid"] for r in outcomes),
            "outcomes": outcomes, "distance_evaluations_upper_bound":
            prioritization_cost(len(probes))}


def analyze(items: list[dict]) -> dict:
    if len(items) != len(PILOT) or {x["program"] for x in items} != set(PILOT):
        raise ValueError("Expected the four distinct pilot programs")
    summary = []
    details = []
    for d in items:
        flags = [bool(x["detected"]) for x in d["outcomes"]]
        order = d["priority_indices"]
        if len(flags) != 12 or sorted(order) != list(range(12)):
            raise ValueError("Invalid oracle result or test order")
        details.append({**d, "detecting_inputs": sum(flags),
                        "budget_results": {
                            str(b): {
                                "fixed": int(any(flags[:b])),
                                "diversity": int(any(flags[x] for x in order[:b])),
                                "uniform_random_probability": probability_hit(sum(flags), b)
                            } for b in BUDGETS}})
    for b in BUDGETS:
        fixed = sum(d["budget_results"][str(b)]["fixed"] for d in details)
        diverse = sum(d["budget_results"][str(b)]["diversity"] for d in details)
        random_exact = sum(d["budget_results"][str(b)]["uniform_random_probability"]
                           for d in details)
        summary.append({"budget": b, "fixed_detected_programs": fixed,
                        "diversity_detected_programs": diverse,
                        "expected_uniform_random_programs": round(random_exact, 6)})
    return {"experiment": "EXP-006A", "status": "pilot_only",
            "scope": "4 known QuixBugs defects; NOT an unbiased benchmark",
            "programs": list(PILOT), "policy": "input-only farthest-first Jaccard",
            "budgets": list(BUDGETS),
            "summary": summary,
            "oracle_invalid_inputs": sum(d["oracle_invalid"] for d in details),
            "details": details}


def run() -> dict:
    items = []
    for name in PILOT:
        worker = subprocess.run(
            [sys.executable, "-m", "lab.quixbugs_diversity", "--child", name],
            text=True, capture_output=True, timeout=WORKER_TIMEOUT_SECONDS,
            check=False, cwd=ROOT)
        if worker.returncode:
            raise RuntimeError(f"Cannot silently exclude pilot {name}: "
                               f"{worker.stderr[-700:]}")
        items.append(json.loads(worker.stdout))
    return analyze(items)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", choices=PILOT)
    parser.add_argument("--output", default="results/exp006a.json")
    args = parser.parse_args(argv)
    if args.child:
        print(json.dumps(evaluate_program(args.child)))
        return
    report = run()
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print("EXP006A_SUMMARY=" + json.dumps({
        "status": report["status"], "programs": report["programs"],
        "summary": report["summary"],
        "oracle_invalid_inputs": report["oracle_invalid_inputs"],
        "orders": {d["program"]: d["priority_indices"] for d in report["details"]}
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
