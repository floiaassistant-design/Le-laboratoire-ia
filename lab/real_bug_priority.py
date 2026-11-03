"""EXP-008A: real historical bug test-prioritization pilot (two projects).

Policies and candidate suite are fixed in experiments/exp008a-manifest.json.
The *same fixed-revision test module* is used against both buggy/fixed code
checkouts. All methods are executed once per revision; policies are evaluated
post hoc on the observed per-test outcomes, so this is a retrospective pilot.

IMPORTANT: imports and executes THIRD-PARTY source in an isolated GitHub
Actions read-only job without persisted credentials. Do not run on user PC.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import json
from math import comb
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Any
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "experiments" / "exp008a-manifest.json"
MARKER = "EXP008A_CHILD="
PROJECT_TIMEOUT_SECONDS = 240
CLONE_TIMEOUT_SECONDS = 150
MAX_TESTS = 250


def validate_manifest(m: dict) -> dict:
    if m.get("experiment") != "EXP-008A":
        raise ValueError("Wrong experiment")
    if m.get("budgets") != [1, 3, 6, 12] or m.get("random_seed") != 20261103:
        raise ValueError("Budgets and seed must remain fixed")
    if m.get("policy_names") != ["lexical","seeded_random","structural_diversity"]:
        raise ValueError("Policy names changed")
    if m.get("test_bank_source") != "fixed_revision_test_file_overlaid_on_both_buggy_and_fixed_sources":
        raise ValueError("Test-bank revision changed")
    cases=m.get("cases")
    if not isinstance(cases,list) or len(cases)!=2:
        raise ValueError("Expected two pinned pilot cases")
    expected=[("youtube-dl-1","ytdl-org/youtube-dl","test/test_utils.py"),
              ("tornado-1","tornadoweb/tornado","tornado/test/websocket_test.py")]
    for case,(id_,repo,file_) in zip(cases,expected):
        if (case["id"],case["repo"],case["test_file"])!=(id_,repo,file_):
            raise ValueError("Unexpected fixed case")
        if case["url"] != "https://github.com/"+repo+".git":
            raise ValueError("Unexpected upstream git URL")
        for key in ("buggy","fixed"):
            if not re.fullmatch("[0-9a-f]{40}",case[key]):
                raise ValueError("Unpinned revision")
        if case["buggy"]==case["fixed"]:
            raise ValueError("Versions identical")
    return m


def manifest() -> dict:
    return validate_manifest(json.loads(MANIFEST.read_text(encoding="utf-8")))


def _bucket(count: int) -> str:
    return "0" if count==0 else "1" if count==1 else "2-3" if count<=3 else "4-7" if count<=7 else "8+"


def method_features(code: str, test_ids: list[str]) -> dict[str, frozenset[str]]:
    """Static AST and identifier features ONLY, no outcomes/patch inspection."""
    tree=ast.parse(code)
    definitions: dict[tuple[str,str], ast.AST]={}
    for node in tree.body:
        if isinstance(node,ast.ClassDef):
            for method in node.body:
                if isinstance(method,(ast.FunctionDef,ast.AsyncFunctionDef)) and method.name.startswith("test_"):
                    definitions[(node.name,method.name)]=method
        elif isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            definitions[("",node.name)]=node
    output={}
    for ident in test_ids:
        pieces=ident.split(".")
        name=pieces[-1]
        owner=pieces[-2] if len(pieces)>1 else ""
        tags={"name:"+part for part in re.findall("[a-z0-9]+",re.sub("([a-z])([A-Z])",r"\1_\2",owner+"_"+name).lower())}
        node=definitions.get((owner,name))
        if node is not None:
            nodes=list(ast.walk(node))
            for kind,cls in [("assert",ast.Assert),("call",ast.Call),("if",ast.If),
                             ("for",ast.For),("with",ast.With),("raise",ast.Raise),
                             ("try",ast.Try)]:
                tags.add(kind+":"+_bucket(sum(isinstance(n,cls) for n in nodes)))
            tags.add("args:"+_bucket(len(node.args.args)))
        else:
            tags.add("no_direct_ast_definition")
        output[ident]=frozenset(tags)
    return output


def _distance(a: frozenset[str],b: frozenset[str]) -> float:
    union=a|b
    return len(a^b)/len(union) if union else 0.0


def policy_orders(ids: list[str],features: dict[str,frozenset[str]],
                  seed: int) -> dict[str,list[str]]:
    if len(set(ids))!=len(ids) or not ids:
        raise ValueError("Test identifiers must be distinct and nonempty")
    names=sorted(ids)
    if set(names)!=set(features):
        raise ValueError("Missing input-only features")
    shuffled=names[:]
    random.Random(seed).shuffle(shuffled)
    d={(a,b):_distance(features[a],features[b]) for a in names for b in names}
    selected=[]
    remaining=set(names)
    while remaining:
        if not selected:
            take=min(remaining,key=lambda x:(-sum(d[x,y] for y in names)/len(names),x))
        else:
            take=min(remaining,key=lambda x:(
                -min(d[x,y] for y in selected),
                -sum(d[x,y] for y in selected)/len(selected),x))
        selected.append(take)
        remaining.remove(take)
    return {"lexical":names,"seeded_random":shuffled,"structural_diversity":selected}


def exact_random_hit(n: int, exposing: int, budget: int) -> float:
    if n<1 or exposing<0 or exposing>n or budget<0 or budget>n:
        raise ValueError("Invalid combinatorial inputs")
    if exposing==0 or budget==0:
        return 0.0
    if n-exposing<budget:
        return 1.0
    return 1-comb(n-exposing,budget)/comb(n,budget)


class RecordingResult(unittest.TestResult):
    """Record pass/fail/error/skip per test without exception tracebacks."""
    def __init__(self):
        super().__init__()
        self.status: dict[str,str]={}

    def startTest(self,test):
        super().startTest(test)
        self.status[test.id()]="started"

    def addSuccess(self,test):
        self.status[test.id()]="pass"
        super().addSuccess(test)

    def addFailure(self,test,err):
        self.status[test.id()]="fail"
        super().addFailure(test,err)

    def addError(self,test,err):
        self.status[test.id()]="error"
        super().addError(test,err)

    def addSkip(self,test,reason):
        self.status[test.id()]="skip"
        super().addSkip(test,reason)

    def addExpectedFailure(self,test,err):
        self.status[test.id()]="xfail"
        super().addExpectedFailure(test,err)

    def addUnexpectedSuccess(self,test):
        self.status[test.id()]="xpass"
        super().addUnexpectedSuccess(test)


def _flatten(suite):
    for x in suite:
        if isinstance(x,unittest.TestSuite):
            yield from _flatten(x)
        else:
            yield x


def child_run(module: str) -> dict:
    # Running this imports and executes THIRD-PARTY test module top-level code.
    loader=unittest.TestLoader()
    suite=loader.loadTestsFromName(module)
    tests=list(_flatten(suite))
    ids=[t.id() for t in tests]
    if loader.errors or not ids or len(ids)>MAX_TESTS or len(set(ids))!=len(ids):
        return {"ok":False,"problem":"invalid_collection",
                "loader_error_count":len(loader.errors),"collected":len(ids)}
    result=RecordingResult()
    suite.run(result)
    unknown=[t.id() for t,_ in result.errors+result.failures if t.id() not in ids]
    return {"ok":not unknown,"problem":"non_case_fixture_error" if unknown else None,
            "total":len(ids),
            "ids":sorted(ids),
            "statuses":{k:result.status.get(k,"missing") for k in sorted(ids)},
            "counts":dict(Counter(result.status.values())),
            "fixture_error_ids":unknown,
            "method_run_count":result.testsRun}


def _execute(cmd: list[str],*,cwd: Path|None=None,timeout: int=120,env: dict|None=None):
    return subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          universal_newlines=True,errors="replace",
                          cwd=cwd,timeout=timeout,check=True,env=env)


def _child_json(root: Path,module: str) -> dict:
    env=os.environ.copy()
    env.update({"PYTHONPATH":os.pathsep.join((str(ROOT),str(root))),
                "PYTHONNOUSERSITE":"1","PYTHONDONTWRITEBYTECODE":"1"})
    cmd=[sys.executable,"-B","-s","-m","lab.real_bug_priority",
         "--child","--module",module]
    run=subprocess.run(cmd,cwd=root,env=env,stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,universal_newlines=True,
                       errors="replace",timeout=PROJECT_TIMEOUT_SECONDS)
    matches=[line[len(MARKER):] for line in run.stdout.splitlines()
             if line.startswith(MARKER)]
    if run.returncode!=0 or len(matches)!=1:
        raise RuntimeError("Child failed to produce one valid JSON record "
                           "(exit %s, stdout tail %s, stderr tail %s)"%
                           (run.returncode,run.stdout[-500:],run.stderr[-800:]))
    report=json.loads(matches[0])
    if not report.get("ok"):
        raise RuntimeError("Invalid third-party collection: "+str(report.get("problem")))
    return report


def run_case(case: dict,seed: int) -> dict:
    """Pin two revisions, use FIXED test module for both, compare same IDs."""
    with TemporaryDirectory(prefix="lab-real-priority-") as tmp:
        base=Path(tmp)
        git=base/"source"
        _execute(["git","-c","core.hooksPath=/dev/null","clone","--quiet",
                 "--filter=blob:none","--no-checkout",case["url"],str(git)],
                 timeout=CLONE_TIMEOUT_SECONDS)
        parent=_execute(["git","-C",str(git),"rev-parse",case["fixed"]+"^"],
                         timeout=30).stdout.strip()
        if parent!=case["buggy"]:
            raise RuntimeError("Fixed commit is not the direct child of buggy revision")
        roots={}
        for name in ("buggy","fixed"):
            root=base/name
            _execute(["git","-c","core.hooksPath=/dev/null","-C",str(git),
                      "worktree","add","--quiet","--detach",str(root),case[name]],
                      timeout=CLONE_TIMEOUT_SECONDS)
            roots[name]=root
        license_text=(roots["fixed"]/case["license_file"]).read_text(encoding="utf-8")
        if case["license"]=="Unlicense":
            valid="unencumbered software" in license_text
        else:
            valid="Apache License" in license_text and "Version 2.0" in license_text
        if not valid:
            raise RuntimeError("Upstream licence cannot be verified")
        test_file=case["test_file"]
        test_code=(roots["fixed"]/test_file).read_text(encoding="utf-8-sig")
        # Overwrite only a working directory copy, never the pinned Git revision.
        shutil.copyfile(str(roots["fixed"]/test_file),str(roots["buggy"]/test_file))
        fixed=_child_json(roots["fixed"],case["module"])
        buggy=_child_json(roots["buggy"],case["module"])
        if fixed["ids"]!=buggy["ids"] or len(fixed["ids"])<12:
            raise RuntimeError("Not a common runnable test universe of >=12 tests")
        ids=fixed["ids"]
        features=method_features(test_code,ids)
        orders=policy_orders(ids,features,seed)
        detected={key:(fixed["statuses"][key]=="pass" and
                       buggy["statuses"][key]=="fail") for key in ids}
        error_changed={key:(fixed["statuses"][key]=="pass" and
                            buggy["statuses"][key]=="error") for key in ids}
        stats={}
        for name,order in orders.items():
            stats[name]={
                "first_12_test_ids":order[:12],
                "by_budget":{str(b):int(any(detected[t] for t in order[:b]))
                             for b in (1,3,6,12)},
                "earliest_detecting_position":next(
                    (i+1 for i,t in enumerate(order) if detected[t]),None)
            }
        return {
            "case":case["id"],"upstream_repo":case["repo"],
            "buggy_commit":case["buggy"],"fixed_commit":case["fixed"],
            "test_bank_revision":"fixed","same_test_file_both_versions":True,
            "historical_python":case["historical_python"],"actual_python":sys.version.split()[0],
            "runtime_test_count":len(ids),
            "source_license_verified":True,
            "fixed_status_counts":fixed["counts"],
            "buggy_status_counts":buggy["counts"],
            "detecting_assertion_test_count":sum(detected.values()),
            "changed_error_not_counted":sum(error_changed.values()),
            "detecting_test_ids":[k for k in ids if detected[k]],
            "source_test_ids":ids,
            "tested_versions":{"buggy":buggy["statuses"],"fixed":fixed["statuses"]},
            "structural_feature_count_unavailable":sum(
                "no_direct_ast_definition" in features[k] for k in ids),
            "policies":stats,
            "exact_uniform_random_expected_hit":{
                str(b):round(exact_random_hit(len(ids),sum(detected.values()),b),9)
                for b in (1,3,6,12)
            },
            "statuses_evaluated_once_per_revision":True,
        }


def run() -> dict:
    data=manifest()
    completed=[]
    failures=[]
    for index,case in enumerate(data["cases"]):
        try:
            completed.append(run_case(case,data["random_seed"]+index))
        except (OSError,ValueError,KeyError,RuntimeError,
                subprocess.TimeoutExpired,subprocess.CalledProcessError) as exc:
            failures.append({"case":case["id"],"problem":type(exc).__name__,
                             "message":str(exc)[-900:]})
    summary=[]
    if len(completed)==len(data["cases"]) and not failures:
        for budget in data["budgets"]:
            row={"budget":budget}
            for policy in data["policy_names"]:
                row[policy]=sum(c["policies"][policy]["by_budget"][str(budget)]
                                for c in completed)
            row["expected_uniform_random"]=round(
                sum(c["exact_uniform_random_expected_hit"][str(budget)]
                    for c in completed),9)
            summary.append(row)
    return {
        "experiment":"EXP-008A",
        "status":"completed" if not failures else "blocked_infrastructure",
        "scope":"retrospective pilot: two known real bugs on two new upstream projects, NOT blind discovery",
        "source_manifest":"experiments/exp008a-manifest.json",
        "project_count":len(completed),
        "failures":failures,
        "summary":summary,
        "cases":completed,
        "methodological_caveats":data["scientific_limits"],
        "agents_evaluated":0,
        "language_models_used":0,
        "independent_bugs_scored":len(completed),
    }


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--child",action="store_true")
    parser.add_argument("--module")
    parser.add_argument("--output",default="results/exp008a-real-priority.json")
    args=parser.parse_args(argv)
    if args.child:
        if args.module not in ("test.test_utils","tornado.test.websocket_test"):
            raise SystemExit("Unexpected third-party test module")
        print(MARKER+json.dumps(child_run(args.module),ensure_ascii=True))
        return
    report=run()
    output=ROOT/args.output
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                      encoding="utf-8")
    print("EXP008A_SUMMARY="+json.dumps({
        "status":report["status"],
        "project_count":report["project_count"],
        "summary":report["summary"],
        "failures":report["failures"],
        "per_case":[{"case":c["case"],"n":c["runtime_test_count"],
                     "detecting":c["detecting_assertion_test_count"],
                     "detecting_test_ids":c["detecting_test_ids"],
                     "first_detection_rank":{
                         name:c["policies"][name]["earliest_detecting_position"]
                         for name in ("lexical","seeded_random","structural_diversity")},
                     "fixed_status_counts":c["fixed_status_counts"],
                     "buggy_status_counts":c["buggy_status_counts"],
                     "changed_error":c["changed_error_not_counted"]}
                    for c in report["cases"]],
        "agents_evaluated":report["agents_evaluated"],
    },ensure_ascii=False))
    if report["failures"]:
        raise SystemExit("Third-party setup or execution failed; see archived JSON")


if __name__=="__main__":
    main()
