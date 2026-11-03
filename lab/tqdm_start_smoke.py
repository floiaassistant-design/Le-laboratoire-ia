"""EXP-006C — reproduce one known tqdm start-offset defect, not a policy score.

The bug metadata comes from BugsInPy; only the separate historical tqdm
source repo is cloned. No dependencies are installed. We run a minimal
standalone regression probe against pinned buggy and fixed commits in a
throwaway directory. Both must execute successfully; only their semantic
outputs should differ. No AI model, secrets, API charges, or benchmark copy.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

from .quixbugs_screen import ROOT
from .realbug_isolation import isolated_python_env, worktree_path

MANIFEST_PATH = ROOT / "experiments" / "exp006c-manifest.json"
SHA = re.compile(r"^[0-9a-f]{40}$")
MARKER = "TQDM_PROBE="
TIMEOUT_SECONDS = 90

# The isolated probe does not import pytest or install any third-party
# dependencies. Its tqdm_class is a transparent progress wrapper that
# deliberately accepts positional and keyword arguments, as permitted by
# the documented extension point. We exercise the *actual upstream*
# tqdm.contrib.tenumerate function in each historical checkout.
PROBE = r'''
import json
import os
import tqdm
from tqdm.contrib import tenumerate

class TransparentProgress:
    def __init__(self, iterable, *args, **kwargs):
        self.iterable = iterable
    def __iter__(self):
        return iter(self.iterable)

repo_root = os.getcwd()
loaded_module = os.path.realpath(tqdm.__file__)
if os.path.commonpath([repo_root, loaded_module]) != repo_root:
    raise RuntimeError("Wrong tqdm module imported: " + loaded_module)

data = list(tenumerate(["a", "b", "c"], start=42,
                       tqdm_class=TransparentProgress))
print("TQDM_PROBE=" + json.dumps({
    "indexes": [index for index, value in data],
    "values": [value for index, value in data]
}, separators=(",", ":")))
'''


def load_manifest():
    return validate_manifest(json.loads(MANIFEST_PATH.read_text(encoding="utf-8")))


def validate_manifest(doc: dict) -> dict:
    if doc.get("experiment") != "EXP-006C-TQDM-REALBUG-CALIBRATION":
        raise ValueError("Unexpected experiment")
    benchmark = doc["source_benchmark"]
    project = doc["upstream_project"]
    case = doc["case"]
    if benchmark["repository"] != "soarsmu/BugsInPy" or benchmark["redistribute_benchmark_source"] is not False:
        raise ValueError("Benchmark provenance or redistribution invalid")
    if benchmark["case_path"] != "projects/tqdm/bugs/1/bug.info":
        raise ValueError("Unexpected benchmark bug")
    if project["repository"] != "tqdm/tqdm" or project["git_url"] != "https://github.com/tqdm/tqdm.git":
        raise ValueError("Unexpected upstream source repository")
    if project["license_path"] != "LICENCE":
        raise ValueError("Unexpected upstream licence file")
    for commit in (benchmark["commit"], case["buggy_commit"], case["fixed_commit"]):
        if not isinstance(commit, str) or not SHA.fullmatch(commit):
            raise ValueError("All revisions must be pinned")
    if case["buggy_commit"] == case["fixed_commit"] or case["id"] != "tqdm-1":
        raise ValueError("Bad bug pair")
    if (case["source_test"] != "tqdm/tests/tests_contrib.py::test_enumerate"
        or case["start"] != 42 or case["input"] != ["a", "b", "c"]
        or case["expected_indexes"] != [42, 43, 44]
        or case["buggy_indexes"] != [0, 1, 2]):
        raise ValueError("Regression test altered")
    flags = doc["interpretation"]
    if (flags["new_bug_discovery"] or flags["policy_comparison"]
        or flags["test_is_official_benchmark_test"]):
        raise ValueError("This is not a held-out experiment")
    return doc


def parse_probe(stdout: str) -> dict | None:
    lines = [line[len(MARKER):] for line in stdout.splitlines()
             if line.startswith(MARKER)]
    if len(lines) != 1:
        return None
    try:
        value = json.loads(lines[0])
        if (not isinstance(value, dict) or
            not isinstance(value.get("indexes"), list) or
            not isinstance(value.get("values"), list)):
            return None
        return value
    except (ValueError, TypeError):
        return None


def verdict(before: dict, after: dict, doc: dict) -> dict:
    case = validate_manifest(doc)["case"]
    b = before.get("parsed")
    a = after.get("parsed")
    before_wrong = (before.get("returncode") == 0
                    and isinstance(b, dict)
                    and b.get("indexes") == case["buggy_indexes"]
                    and b.get("values") == case["input"])
    after_correct = (after.get("returncode") == 0
                     and isinstance(a, dict)
                     and a.get("indexes") == case["expected_indexes"]
                     and a.get("values") == case["input"])
    return {"buggy_wrong_start_reproduced": bool(before_wrong),
            "fixed_start_correct": bool(after_correct),
            "bug_reproduced": bool(before_wrong and after_correct)}


def _command(command: list[str], timeout: int = TIMEOUT_SECONDS,
             cwd: Path | None = None, env=None):
    return subprocess.run(command, capture_output=True, text=True,
                          errors="replace", timeout=timeout, cwd=cwd, env=env,
                          check=True)


def run() -> dict:
    manifest = load_manifest()
    case = manifest["case"]
    report = {
        "experiment": "EXP-006C",
        "case_id": case["id"],
        "upstream_project": manifest["upstream_project"]["repository"],
        "source_benchmark": manifest["source_benchmark"]["repository"],
        "buggy_commit": case["buggy_commit"],
        "fixed_commit": case["fixed_commit"],
        "python_version": sys.version.split()[0],
        "historical_python_declared": case["historical_python"],
        "kind": "known published bug calibration (not benchmark scoring)",
        "upstream_tests_executed": False,
        "upstream_dependencies_installed": False,
        "upstream_source_redistributed": False,
        "revision_worktrees_isolated": True,
        "python_bytecode_disabled": True,
        "runs": {},
        "bug_reproduced": False,
    }
    if sys.version_info[:2] != (3, 8):
        report["blocker"] = "Python 3.8 required for this CI smoke test"
        return report
    with TemporaryDirectory(prefix="laboratoire-tqdm-") as folder:
        source = Path(folder) / "tqdm"
        _command(["git", "-c", "core.hooksPath=/dev/null", "clone", "--quiet",
                  "--filter=blob:none", "--no-checkout",
                  manifest["upstream_project"]["git_url"], str(source)])
        parent = _command(["git", "-C", str(source), "rev-parse",
                           case["fixed_commit"] + "^"]).stdout.strip()
        if parent != case["buggy_commit"]:
            report["blocker"] = "Not a direct parent bug/fix pair"
            return report
        report["fix_parent_verified"] = True
        for label, sha in (("buggy", case["buggy_commit"]), ("fixed", case["fixed_commit"])):
            # Never swap files underneath the same Python __pycache__ directory.
            # Same-size source files plus second-resolution mtimes can reuse a
            # stale .pyc from the previously checked-out historical commit.
            checkout = worktree_path(Path(folder), label)
            checkout.parent.mkdir(parents=True, exist_ok=True)
            _command(["git", "-c", "core.hooksPath=/dev/null", "-C",
                      str(source), "worktree", "add", "--quiet", "--detach",
                      str(checkout), sha])
            licence = (checkout / manifest["upstream_project"]["license_path"]).read_text(
                encoding="utf-8")
            if "Mozilla Public Licence" not in licence or "MIT License" not in licence:
                report["blocker"] = "Historical source licence not verified"
                return report
            env = isolated_python_env(checkout)
            result = subprocess.run([sys.executable, "-B", "-s", "-c", PROBE],
                                    cwd=checkout, env=env, capture_output=True,
                                    text=True, errors="replace", timeout=20)
            report["runs"][label] = {
                "returncode": result.returncode,
                "parsed": parse_probe(result.stdout),
                "stdout_tail": result.stdout[-700:],
                "stderr_tail": result.stderr[-1000:]}
        report["historical_source_licence_verified"] = True
    report.update(verdict(report["runs"]["buggy"], report["runs"]["fixed"], manifest))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--output", default="results/exp006c-tqdm-smoke.json")
    args = parser.parse_args(argv)
    if args.offline == args.online:
        parser.error("Select exactly one of --offline or --online")
    if args.offline:
        validate_manifest(load_manifest())
        print("EXP006C_MANIFEST_VALID=true")
        return
    try:
        report = run()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        report = {"experiment": "EXP-006C", "bug_reproduced": False,
                  "blocker": type(exc).__name__,
                  "notes": "Infrastructure/setup failure; no bug detection may be claimed"}
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print("EXP006C_RESULT=" + json.dumps({
        "bug_reproduced": report["bug_reproduced"],
        "python_version": report.get("python_version"),
        "blocker": report.get("blocker"),
        "before": report.get("runs", {}).get("buggy", {}).get("parsed"),
        "after": report.get("runs", {}).get("fixed", {}).get("parsed"),
    }, ensure_ascii=False))
    if report.get("bug_reproduced") is not True:
        raise SystemExit("Independent project bug not reproduced; do not score policies")


if __name__ == "__main__":
    main()
