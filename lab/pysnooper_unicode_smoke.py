"""EXP-006B: one real historical bug reproduction smoke test.

Uses MIT-licensed PySnooper source at two pinned commits from BugsInPy
metadata. Clones *source only*, never installs its dependencies or executes
upstream setup/test scripts. A short independent regression probe exercises
the Unicode log-writing symptom under an ASCII locale. This is NOT an
unbiased benchmark and NOT a test-selection policy comparison.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from .external_corpus_preflight import load_manifest, ROOT
from .realbug_isolation import isolated_python_env, worktree_path

REPOSITORY = "https://github.com/cool-RR/PySnooper.git"
SUCCESS_MARKER = "PYSNOOPER_UNICODE_OK"
OLD_FAILURE = "UnicodeEncodeError"
TIMEOUT_SECONDS = 105

# Executed only in the temporary MIT-licensed source checkout, in an
# isolated GitHub Actions job without secrets or repository write access.
PROBE = r"""
import locale
import tempfile
from pathlib import Path
import pysnooper

enc = locale.getpreferredencoding(False)
if not enc.lower() in ("ansi_x3.4-1968", "us-ascii", "ascii"):
    raise RuntimeError("Expected ASCII locale, got " + enc)

with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "trace.log"
    @pysnooper.snoop(path)
    def exercise():
        word = "\u5931\u8d25"
        return word

    assert exercise() == "\u5931\u8d25"
    content = path.read_text(encoding="utf-8")
    assert "\u5931\u8d25" in content, "Unicode not preserved in trace"

print("PYSNOOPER_UNICODE_OK")
"""


def success_evidence(old: dict, fixed: dict) -> dict:
    old_specific = old.get("returncode") not in (None, 0) and OLD_FAILURE in old.get("stderr", "")
    fix_specific = fixed.get("returncode") == 0 and SUCCESS_MARKER in fixed.get("stdout", "")
    return {"old_failed_with_unicode_error": old_specific,
            "fixed_passed_unicode_probe": fix_specific,
            "bug_reproduced": bool(old_specific and fix_specific)}


def _run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 90,
         env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                          timeout=timeout, check=True, errors="replace")


def run_smoke() -> dict:
    manifest = load_manifest()
    case = next(x for x in manifest["cases"] if x["id"] == "PySnooper-1")
    result = {
        "experiment": "EXP-006B-REALBUG-SMOKE",
        "source": "BugsInPy PySnooper-1, metadata SHA " + manifest["dataset"]["commit"],
        "source_repository": REPOSITORY,
        "python_version": sys.version.split()[0],
        "buggy_commit": case["buggy"],
        "fixed_commit": case["fixed"],
        "conditions": "LC_ALL=C, PYTHONUTF8=0, PYTHONCOERCECLOCALE=0",
        "regression_probe": "Minimal custom Unicode trace assertion; not official BugsInPy test",
        "third_party_code_copied_into_repo": False,
        "third_party_setup_or_tests_executed": False,
        "revision_worktrees_isolated": True,
        "python_bytecode_disabled": True,
        "policies_compared": False,
        "outcomes": {},
        "bug_reproduced": False,
    }
    if sys.version_info[:2] != (3, 8):
        result["blocker"] = "This calibration requires a Python 3.8 interpreter."
        return result

    with TemporaryDirectory(prefix="lab-pysnooper-") as folder:
        source = Path(folder) / "PySnooper"
        _run(["git", "-c", "core.hooksPath=/dev/null", "clone",
              "--quiet", "--filter=blob:none", "--no-checkout", REPOSITORY,
              str(source)], timeout=TIMEOUT_SECONDS)
        for label, sha in (("buggy", case["buggy"]), ("fixed", case["fixed"])):
            checkout = worktree_path(Path(folder), label)
            checkout.parent.mkdir(parents=True, exist_ok=True)
            _run(["git", "-c", "core.hooksPath=/dev/null", "-C", str(source),
                  "worktree", "add", "--quiet", "--detach", str(checkout), sha],
                 timeout=TIMEOUT_SECONDS)
            env = isolated_python_env(checkout)
            env.update({"LC_ALL": "C", "LANG": "C",
                        "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"})
            completed = subprocess.run([sys.executable, "-B", "-c", PROBE],
                                       cwd=checkout, env=env,
                                       capture_output=True, text=True,
                                       timeout=15, errors="replace")
            result["outcomes"][label] = {
                "returncode": completed.returncode,
                "stdout": completed.stdout[-600:],
                "stderr": completed.stderr[-1800:],
            }
    result.update(success_evidence(result["outcomes"]["buggy"], result["outcomes"]["fixed"]))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--online", action="store_true", required=True)
    parser.add_argument("--output", default="results/exp006b-realbug-smoke.json")
    args = parser.parse_args(argv)
    try:
        report = run_smoke()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        report = {"experiment": "EXP-006B-REALBUG-SMOKE",
                  "bug_reproduced": False,
                  "blocker": type(error).__name__,
                  "notes": "Failure must be investigated; do not count a detected bug."}
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print("EXP006B_REALBUG=" + json.dumps({
        "bug_reproduced": report["bug_reproduced"],
        "blocker": report.get("blocker"),
        "old_failed_with_unicode_error": report.get("old_failed_with_unicode_error"),
        "fixed_passed_unicode_probe": report.get("fixed_passed_unicode_probe"),
        "python_version": report.get("python_version"),
    }, ensure_ascii=False))
    if report["bug_reproduced"] is not True:
        raise SystemExit("Real-bug calibration not confirmed; cannot score policies.")


if __name__ == "__main__":
    main()
