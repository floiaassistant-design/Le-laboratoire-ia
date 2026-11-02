"""EXP-004A: calibration on independently authored QuixBugs benchmark fixtures.

Screens whether the FIXED code agrees with a fixture and whether the BUGGY code
fails it. Does not compare the EXP-003 probe-selection strategies.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import runpy
import signal
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "third_party" / "quixbugs"
PROGRAMS = (
    "bitcount", "bucketsort", "find_first_in_sorted", "find_in_sorted",
    "flatten", "gcd", "get_factors", "hanoi", "is_valid_parenthesization",
    "kth", "lcs_length", "levenshtein", "lis", "longest_common_subsequence",
    "max_sublist_sum", "mergesort", "next_palindrome", "next_permutation",
    "pascal", "powerset",
)

class Deadline(Exception):
    """A single candidate ran beyond its fixed time budget."""


def canonical(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return [canonical(x) for x in value]
    if isinstance(value, (set, frozenset)):
        return sorted((canonical(x) for x in value), key=repr)
    if isinstance(value, dict):
        return {str(k): canonical(v) for k, v in value.items()}
    return value


def read_fixtures(path: Path) -> list[tuple[list[Any], Any]]:
    """QuixBugs stores one [arguments, expected] JSON record per line."""
    fixtures = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        args, expected = json.loads(line)
        if not isinstance(args, list):
            raise ValueError(f"{path}:{line_number}: positional args must be a list")
        fixtures.append((args, expected))
    return fixtures


def _on_alarm(_signum, _frame):
    raise Deadline("call timed out")


def invoke(func, args: list[Any], timeout_seconds: float = .25) -> dict[str, Any]:
    """Linux-only per-call time limit; subprocess gives a second safety layer."""
    previous = signal.signal(signal.SIGALRM, _on_alarm)
    old_timer = signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
    try:
        with redirect_stdout(StringIO()):
            result = func(*deepcopy(args))
        return {"status": "ok", "value": canonical(result)}
    except Deadline:
        return {"status": "timeout"}
    except Exception as exc:
        return {"status": "exception", "error": type(exc).__name__}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        if old_timer[0] or old_timer[1]:
            signal.setitimer(signal.ITIMER_REAL, *old_timer)


def load_function(kind: str, name: str):
    if name not in PROGRAMS or kind not in ("buggy", "correct"):
        raise ValueError("invalid corpus target")
    with redirect_stdout(StringIO()):
        module = runpy.run_path(str(DATA / kind / f"{name}.py"))
    return module[name]


def evaluate_program(name: str) -> dict[str, Any]:
    fixtures = read_fixtures(DATA / "fixtures" / f"{name}.json")
    try:
        fixed, buggy = load_function("correct", name), load_function("buggy", name)
    except Exception as e:
        return {"program": name, "status": "load_error", "error": type(e).__name__, "fixtures": len(fixtures)}
    valid = invalid = detected = buggy_timeouts = buggy_exceptions = 0
    for args, expected in fixtures:
        reference = invoke(fixed, args)
        if reference["status"] != "ok" or reference["value"] != canonical(expected):
            invalid += 1
            continue
        valid += 1
        candidate = invoke(buggy, args)
        if candidate["status"] == "timeout":
            buggy_timeouts += 1
        if candidate["status"] == "exception":
            buggy_exceptions += 1
        if candidate["status"] != "ok" or candidate["value"] != reference["value"]:
            detected += 1
    return {"program": name, "status": "evaluated", "fixtures": len(fixtures),
            "reference_valid": valid, "reference_invalid": invalid,
            "bug_exposing_fixtures": detected, "bug_detected": bool(detected),
            "buggy_timeouts": buggy_timeouts, "buggy_exceptions": buggy_exceptions}


def run_screen(timeout_per_program: int = 15) -> dict[str, Any]:
    if timeout_per_program < 1:
        raise ValueError("invalid per-program timeout")
    programs = []
    for name in PROGRAMS:
        try:
            child = subprocess.run([sys.executable, "-m", "lab.quixbugs_screen", "--child", name],
                text=True, capture_output=True, timeout=timeout_per_program, cwd=ROOT,
                check=False)
            if child.returncode:
                data = {"program": name, "status": "worker_error", "returncode": child.returncode}
            else:
                data = json.loads(child.stdout)
        except subprocess.TimeoutExpired:
            data = {"program": name, "status": "worker_timeout"}
        programs.append(data)
    evaluated = [p for p in programs if p["status"] == "evaluated"]
    eligible = [p for p in evaluated if p["reference_valid"] > 0]
    detectable = sum(p["bug_detected"] for p in eligible)
    return {"experiment": "EXP-004A", "benchmark": "QuixBugs", "source_commit":
        "4257f44b0ff1181dedaedee6a447e133219fcebf",
        "claim_scope": "Coverage calibration with benchmark-provided testcases only; not a comparison of testing policies or LLM agents",
        "requested_programs": len(PROGRAMS), "evaluated_programs": len(evaluated),
        "eligible_programs": len(eligible), "detectable_programs": detectable,
        "programs": programs}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", choices=PROGRAMS)
    parser.add_argument("--output", default="results/exp004a.json")
    args = parser.parse_args(argv)
    if args.child:
        print(json.dumps(evaluate_program(args.child), ensure_ascii=False))
        return
    report = run_screen()
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "programs"}, ensure_ascii=False))
    print("PROGRAM_ROWS=" + json.dumps(report["programs"], ensure_ascii=False))
    if report["eligible_programs"] < 10:
        raise SystemExit("Too few valid reference programs; investigate corpus compatibility")

if __name__ == "__main__":
    main()
