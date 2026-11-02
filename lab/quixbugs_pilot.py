"""EXP-004B pilot: locked policies on four QuixBugs programs.

No canonical QuixBugs json fixtures are imported for selecting inputs.
This is a *pilot*, not the held-out 16-program final comparison.

Execute: python -m lab.quixbugs_pilot
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from json import dumps
from pathlib import Path
from random import Random
import subprocess
import sys

from .quixbugs_screen import ROOT, PROGRAMS, invoke, load_function

PILOT = ("bitcount", "gcd", "find_first_in_sorted", "bucketsort")
HOLDOUT = tuple(n for n in PROGRAMS if n not in PILOT)
SEED = 20261102
REPEATS = 40
BUDGETS = (1, 3, 6, 12)
METHODS = ("random", "targeted", "hybrid")
MAX_CALL_SECONDS = 0.03


def domain_probes(name: str) -> tuple[tuple, ...]:
    """From API contracts / types only; fixed before looking at pilot scores."""
    if name == "bitcount":
        return tuple((n,) for n in (0, 1, 2, 3, 7, 8, 15, 16, 31, 32, 63, 64))
    if name == "gcd":
        return ((0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (8, 12),
                (12, 8), (25, 5), (5, 25), (97, 89), (100, 1), (100, 0))
    if name == "find_first_in_sorted":
        return (([], 0), ([0], 0), ([0], 1), ([0, 0], 0),
                ([1, 2, 3], 1), ([1, 2, 3], 3),
                ([1, 2, 3], 4), ([1, 1, 2], 1),
                ([-2, -1, 0], -2), ([-2, -1, 0], 0),
                ([5, 5, 5], 5), ([-1, 0, 1], -3))
    if name == "bucketsort":
        return (([], 1), ([0], 1), ([1, 0], 2), ([0, 0], 1),
                ([2, 1, 2], 3), ([0, 2, 1], 3), ([1], 2),
                ([3, 1, 2], 4), ([0, 0, 0], 1),
                ([5, 4, 3], 6), ([3, 3, 1], 4), ([], 10))
    raise ValueError("Only the predeclared four pilot functions are permitted")


def random_probe(name: str, rng: Random) -> tuple:
    if name == "bitcount":
        return (rng.randint(0, 65535),)
    if name == "gcd":
        return (rng.randint(0, 200), rng.randint(0, 200))
    if name == "find_first_in_sorted":
        xs = sorted(rng.randint(-20, 20) for _ in range(rng.randint(0, 16)))
        return (xs, rng.randint(-20, 20))
    if name == "bucketsort":
        k = rng.randint(1, 16)
        return ([rng.randrange(k) for _ in range(rng.randint(0, 18))], k)
    raise ValueError("Only predeclared pilots are supported")


def generate(name: str, method: str, budget: int, seed: int) -> list[tuple]:
    if name not in PILOT or method not in METHODS or budget not in BUDGETS:
        raise ValueError("unknown pilot/method/budget")
    edge = domain_probes(name)
    edge_count = (0 if method == "random" else
                  budget if method == "targeted" else min(3, budget))
    rng = Random(seed)
    return list(edge[:edge_count]) + [
        random_probe(name, rng) for _ in range(budget - edge_count)]


def check_one(fixed, buggy, inputs: list[tuple]) -> dict:
    tested = invalid = exceptions = timeouts = 0
    detected = False
    for args in inputs:
        tested += 1  # max budget includes invalid inputs
        oracle = invoke(fixed, list(args), MAX_CALL_SECONDS)
        if oracle["status"] != "ok":
            invalid += 1
            continue
        candidate = invoke(buggy, list(args), MAX_CALL_SECONDS)
        if candidate["status"] == "timeout":
            timeouts += 1
        if candidate["status"] == "exception":
            exceptions += 1
        if candidate["status"] != "ok" or candidate["value"] != oracle["value"]:
            detected = True
            break
    return {"detected": detected, "used": tested, "invalid": invalid,
            "buggy_timeouts": timeouts, "buggy_exceptions": exceptions}


def evaluate_program(name: str) -> dict:
    if name not in PILOT:
        raise ValueError("Do not touch held-out programs during pilot")
    correct, buggy = load_function("correct", name), load_function("buggy", name)
    results = []
    for budget in BUDGETS:
        for repeat in range(REPEATS):
            seed = SEED + 100003 * repeat + 47 * PILOT.index(name)
            for method in METHODS:
                # Random subsequence shared between methods, not tuned to result.
                row = check_one(correct, buggy, generate(name, method, budget, seed))
                results.append({"program": name, "budget": budget,
                                "repeat": repeat, "method": method, **row})
    return {"program": name, "observations": results}


def run() -> dict:
    rows = []
    for name in PILOT:
        # Process barrier prevents one bad program from stalling the entire pilot.
        child = subprocess.run(
            [sys.executable, "-m", "lab.quixbugs_pilot", "--child", name],
            capture_output=True, text=True, timeout=40, cwd=ROOT)
        if child.returncode:
            raise RuntimeError(f"Pilot worker failed for {name}: {child.stderr[-1200:]}")
        from json import loads
        rows.extend(loads(child.stdout)["observations"])
    aggregate = []
    for budget in BUDGETS:
        for method in METHODS:
            matches = [r for r in rows if r["budget"] == budget and r["method"] == method]
            detected = sum(r["detected"] for r in matches)
            unique_programs = sum(
                any(r["detected"] for r in matches if r["program"] == name)
                for name in PILOT)
            aggregate.append({
                "budget": budget, "method": method,
                "detections": detected, "trials": len(matches),
                "detection_rate": round(detected / len(matches), 5),
                "programs_detected_at_least_once": unique_programs,
                "calls_used": sum(r["used"] for r in matches),
                "invalid_calls": sum(r["invalid"] for r in matches),
                "timeouts": sum(r["buggy_timeouts"] for r in matches),
                "exceptions": sum(r["buggy_exceptions"] for r in matches),
            })
    return {
        "experiment": "EXP-004B-PILOT", "external_benchmark": "QuixBugs",
        "upstream_commit": "4257f44b0ff1181dedaedee6a447e133219fcebf",
        "seed": SEED, "repeats_per_program": REPEATS, "budgets": list(BUDGETS),
        "pilot_programs": list(PILOT), "reserved_programs": list(HOLDOUT),
        "methods": list(METHODS), "max_call_seconds": MAX_CALL_SECONDS,
        "scope": "Pilot feasibility only, NOT a blind independent policy validation",
        "aggregate": aggregate, "observations": rows,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", choices=PILOT)
    parser.add_argument("--output", default="results/exp004b-pilot.json")
    args = parser.parse_args(argv)
    if args.child:
        print(dumps(evaluate_program(args.child)))
        return
    result = run()
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PILOT_AGGREGATE=" + dumps(result["aggregate"], ensure_ascii=False))
    print("PILOT_INFO=" + dumps(
        {k: v for k, v in result.items() if k not in ("aggregate", "observations")},
        ensure_ascii=False))


if __name__ == "__main__":
    main()
