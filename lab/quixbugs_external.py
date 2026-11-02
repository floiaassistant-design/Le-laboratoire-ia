"""EXP-004B external-policy comparison (16 QuixBugs programs).

The generators use input contracts, not benchmark fixture rows. The bugs were
previously visible to the research author: this is NOT a blind experiment.
Do not change the policies after seeing the results.

Run: python -m lab.quixbugs_external
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from random import Random
import subprocess
import sys

from .quixbugs_pilot import HOLDOUT, PILOT, check_one, METHODS
from .quixbugs_screen import ROOT, load_function

PROGRAMS = HOLDOUT
SEED = 20261102
REPEATS = 10
BUDGETS = (1, 3, 6, 12)
TIMEOUT_SECONDS = 45

def edge_probes(name: str) -> tuple[tuple, ...]:
    """Twelve contract-derived edge/structural probes, fixed before scoring."""
    cases = {
        "find_in_sorted": (
            ([], 0), ([0], 0), ([0], 1), ([0, 0], 0),
            ([1, 2, 3], 1), ([1, 2, 3], 3), ([1, 2, 3], 4),
            ([1, 1, 2], 1), ([-2, -1, 0], -2), ([-2, -1, 0], 0),
            ([5, 5, 5], 5), ([-1, 0, 1], -3)),
        "flatten": (
            ([],), ([1],), ([[1]],), ([[], []],),
            ([1, [2]],), ([[1, [2]], 3],), ([0, [0]],),
            ([["a"], "b"],), ([[[[1]]]],), ([1, [], 2],),
            ([[], 1],), ([[1, 2], [3, 4]],)),
        "get_factors": tuple((x,) for x in (
            1, 2, 3, 4, 5, 6, 8, 9, 12, 25, 97, 100)),
        "hanoi": (
            (0, 1, 3), (1, 1, 3), (2, 1, 3), (3, 1, 3),
            (4, 1, 3), (1, 2, 3), (2, 2, 3), (3, 2, 3),
            (1, 3, 2), (2, 3, 2), (0, 1, 2), (5, 1, 3)),
        "is_valid_parenthesization": tuple((s,) for s in (
            "", "()", "(", ")", "(())", "()()", "(()", "())",
            ")(", "((()))", "())(", "()(()())")),
        "kth": (
            ([1], 0), ([1, 2], 0), ([1, 2], 1),
            ([2, 1], 0), ([2, 1], 1), ([1, 1], 0),
            ([1, 1], 1), ([1, 2, 3], 0), ([1, 2, 3], 2),
            ([3, 1, 2], 1), ([2, 2, 2], 2), ([-2, 0, 4], 1)),
        "lcs_length": tuple((a, b) for a, b in (
            ("", ""), ("a", ""), ("", "a"), ("a", "a"),
            ("a", "b"), ("ab", "ba"), ("abc", "abc"),
            ("abc", "xyz"), ("aaaa", "aa"), ("abc", "bc"),
            ("abc", "ac"), ("abab", "baba"))),
        "levenshtein": tuple((a, b) for a, b in (
            ("", ""), ("a", ""), ("", "b"), ("a", "a"),
            ("a", "b"), ("ab", "ba"), ("abc", "abc"),
            ("abc", "ab"), ("abc", "axc"), ("aa", "aaa"),
            ("abcd", "efgh"), ("abc", "cab"))),
        "lis": tuple((a,) for a in (
            [], [1], [2, 1], [1, 2], [1, 1],
            [3, 2, 1], [1, 2, 3], [1, 3, 2], [0, 0, 0],
            [3, -1, 2], [5, 1, 4, 2, 3], [2, 2, 3, 1])),
        "longest_common_subsequence": tuple((a, b) for a, b in (
            ("", ""), ("a", ""), ("", "b"), ("a", "a"),
            ("a", "b"), ("ab", "ba"), ("abc", "abc"),
            ("abc", "xyz"), ("abc", "ac"), ("aabc", "abc"),
            ("abc", "cab"), ("abba", "baba"))),
        "max_sublist_sum": tuple((a,) for a in (
            [], [0], [1], [-1], [-1, -2], [1, -1],
            [-1, 1], [1, 2, 3], [-3, 2, -1],
            [4, -10, 3, 2], [0, 0, 0], [-2, 3, -1, 3])),
        "mergesort": tuple((a,) for a in (
            [], [1], [2, 1], [1, 2], [1, 1],
            [3, 2, 1], [1, 2, 3], [2, 2, 2], [0, -1, 1],
            [3, 1, 2], [5, 2, 5, 1], [-1, -3, -2])),
        "next_palindrome": tuple((a,) for a in (
            [0], [1], [9], [1, 1], [9, 9], [1, 0, 1],
            [1, 1, 1], [9, 9, 9], [1, 2, 2, 1],
            [9, 0, 0, 9], [1, 2, 3, 2, 1], [9, 9, 9, 9])),
        "next_permutation": tuple((a,) for a in (
            [], [1], [1, 2], [2, 1], [1, 2, 3],
            [3, 2, 1], [1, 3, 2], [2, 1, 3], [3, 1, 2],
            [2, 3, 1], [4, 3, 2, 1], [1, 2, 4, 3])),
        "pascal": tuple((x,) for x in (
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)),
        "powerset": tuple((a,) for a in (
            [], [1], [1, 2], [2, 1], [1, 1], [0, 1, 2],
            [1, 2, 3], [1, 2, 3, 4], [0, 0], [2, 2, 3],
            [-1, 0, 1], [1, 1, 1])),
    }
    if name not in PROGRAMS:
        raise ValueError(f"Not a reserved program: {name}")
    result = cases[name]
    if len(result) != 12:
        raise AssertionError(f"Expected 12 boundary probes for {name}")
    return result

def random_probe(name: str, rng: Random) -> tuple:
    if name == "find_in_sorted":
        arr = sorted(rng.randint(-20, 20) for _ in range(rng.randint(0, 12)))
        return (arr, rng.randint(-20, 20))
    if name == "flatten":
        def nested(depth=0):
            n = rng.randint(0, 4)
            return [nested(depth+1) if depth < 3 and rng.random() < .35
                    else rng.randint(-10, 10) for _ in range(n)]
        return (nested(),)
    if name == "get_factors":
        return (rng.randint(1, 500),)
    if name == "hanoi":
        start = rng.randint(1, 3)
        end = rng.choice([x for x in (1, 2, 3) if x != start])
        return (rng.randint(0, 5), start, end)
    if name == "is_valid_parenthesization":
        return ("".join(rng.choices("()", k=rng.randint(0, 12))),)
    if name == "kth":
        arr = [rng.randint(-10, 10) for _ in range(rng.randint(1, 12))]
        return (arr, rng.randrange(len(arr)))
    if name in ("lcs_length", "levenshtein", "longest_common_subsequence"):
        max_len = 5 if name != "lcs_length" else 8
        return tuple("".join(rng.choices("abc", k=rng.randint(0, max_len)))
                     for _ in range(2))
    if name in ("lis", "max_sublist_sum", "mergesort"):
        return ([rng.randint(-10, 10) for _ in range(rng.randint(0, 12))],)
    if name == "next_palindrome":
        size = rng.randint(1, 6)
        arr = [rng.randrange(10) for _ in range((size + 1) // 2)]
        return (arr + arr[-(size // 2):][::-1],)
    if name == "next_permutation":
        return (rng.sample(range(1, 9), rng.randint(0, 6)),)
    if name == "pascal":
        return (rng.randint(1, 12),)
    if name == "powerset":
        return ([rng.randint(-5, 5) for _ in range(rng.randint(0, 6))],)
    raise ValueError(f"Unknown program: {name}")

def generate(name: str, method: str, budget: int, seed: int) -> list[tuple]:
    if name not in PROGRAMS or method not in METHODS or budget not in BUDGETS:
        raise ValueError("Invalid program, method or budget")
    edges = edge_probes(name)
    count = 0 if method == "random" else (budget if method == "targeted" else min(3, budget))
    rng = Random(seed)
    return list(edges[:count]) + [random_probe(name, rng)
                                  for _ in range(budget - count)]

def evaluate_program(name: str) -> dict:
    if name not in PROGRAMS:
        raise ValueError("Not a reserved program")
    fixed, buggy = load_function("correct", name), load_function("buggy", name)
    rows = []
    for budget in BUDGETS:
        for repeat in range(REPEATS):
            seed = SEED + 100_003 * repeat + 47 * PROGRAMS.index(name)
            for method in METHODS:
                outcome = check_one(fixed, buggy, generate(name, method, budget, seed))
                rows.append({"program": name, "budget": budget, "repeat": repeat,
                             "method": method, **outcome})
    return {"program": name, "observations": rows}

def execute() -> dict:
    rows = []
    failures = []
    for name in PROGRAMS:
        try:
            child = subprocess.run(
                [sys.executable, "-m", "lab.quixbugs_external", "--child", name],
                capture_output=True, text=True, timeout=TIMEOUT_SECONDS, cwd=ROOT)
            if child.returncode:
                failures.append({"program": name, "reason": "worker_error",
                                 "stderr": child.stderr[-300:]})
            else:
                rows.extend(json.loads(child.stdout)["observations"])
        except subprocess.TimeoutExpired:
            failures.append({"program": name, "reason": "worker_timeout"})
    grouped = []
    for budget in BUDGETS:
        for method in METHODS:
            matches = [x for x in rows if x["budget"] == budget and x["method"] == method]
            counts = {p: sum(x["detected"] for x in matches if x["program"] == p)
                      for p in PROGRAMS}
            grouped.append({
                "budget": budget, "method": method,
                "sum_detected": sum(counts.values()),
                "total_trials": len(matches),
                "detected_programs_at_least_once": sum(v > 0 for v in counts.values()),
                "programs_with_100pct_detection": sum(v == REPEATS for v in counts.values()),
                "per_program": counts,
                "invalid_oracle_calls": sum(x["invalid"] for x in matches),
                "total_calls_used": sum(x["used"] for x in matches),
            })
    return {
        "experiment": "EXP-004B-EXTERNAL", "benchmark": "QuixBugs",
        "upstream": "4257f44b0ff1181dedaedee6a447e133219fcebf",
        "seed": SEED, "budgets": BUDGETS, "repeats_per_program": REPEATS,
        "methods": METHODS, "programs_requested": PROGRAMS,
        "excluded_pilot": PILOT, "failures": failures,
        "methodology": "Policy study on benchmark authored by third parties; not genuinely blind to researcher; no agents or LLMs",
        "aggregates": grouped, "observations": rows,
    }

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--child", choices=PROGRAMS)
    ap.add_argument("--output", default="results/exp004b-external.json")
    args = ap.parse_args(argv)
    if args.child:
        print(json.dumps(evaluate_program(args.child)))
        return
    report = execute()
    dest = ROOT / args.output
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("EXTERNAL_SUMMARY=" + json.dumps({
        "programs_requested": len(PROGRAMS),
        "programs_executed": len(PROGRAMS)-len(report["failures"]),
        "failures": report["failures"],
        "aggregates": report["aggregates"],
    }))
    if report["failures"]:
        raise SystemExit("Research worker failures: must investigate before reporting a complete comparison")

if __name__ == "__main__":
    main()
