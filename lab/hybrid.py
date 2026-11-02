"""EXP-003 hybrid probe allocation; no LLM or external API calls."""
import json
from pathlib import Path
from random import Random
from .cases import CASES,Case
from .robustness import OTHER_MUTANTS
from .experiment import detect
from .holdout import HOLDOUT

SEED=20261102
BUDGET=12
RUNS=200
ALLOCATION=(0,3,6,9,12)

def training_cases():
    negatives=[Case(c.name+"/interieur",c.description,c.reference,
                    OTHER_MUTANTS[c.name],c.random_input,c.edge_inputs)
               for c in CASES if c.name in OTHER_MUTANTS]
    return (*CASES,*negatives)

def probes(case,edges,rng,budget=BUDGET):
    if not 0<=edges<=budget: raise ValueError("edge allocation must be 0..budget")
    planned=list(case.edge_inputs[:edges])
    return planned+[case.random_input(rng) for _ in range(budget-len(planned))]

def evaluate(cases,allocations=ALLOCATION,runs=RUNS,budget=BUDGET,seed=SEED):
    if runs<1 or budget<1: raise ValueError("runs and budget must be positive")
    if any(not 0<=x<=budget for x in allocations): raise ValueError("allocation outside budget")
    results={x:{"detected":0,"total":0,"by_case":{}} for x in allocations}
    for i,case in enumerate(cases):
        for x in allocations:
            hits=0
            for run in range(runs):
                rng=Random(seed+100_003*run+37*i)
                hits+=int(detect(case,probes(case,x,rng,budget)))
            m=results[x]
            m["detected"]+=hits
            m["total"]+=runs
            m["by_case"][case.name]=round(hits/runs,6)
    for m in results.values():
        m["rate"]=round(m["detected"]/m["total"],6)
    return {str(k):v for k,v in results.items()}

def execute(runs=RUNS,budget=BUDGET,seed=SEED):
    if budget!=BUDGET: raise ValueError("EXP-003 preregistered at budget=12")
    train=evaluate(training_cases(),runs=runs,budget=budget,seed=seed)
    best=max(ALLOCATION,key=lambda k:(train[str(k)]["rate"],-k))
    holdout=evaluate(HOLDOUT,allocations=(0,best,12),runs=runs,budget=budget,
                     seed=seed+909_091)
    return {"experiment":"EXP-003","seed":seed,"runs":runs,
            "budget_per_case":budget,"allocations":ALLOCATION,
            "training_cases":len(training_cases()),"holdout_cases":len(HOLDOUT),
            "selection_rule":"maximum pooled train detection, ties prefer fewer edge tests",
            "selected_edges":best,"training":train,"holdout":holdout,
            "note":"Synthetic mutation testing; no LLMs or independent agents were called. Holdout was authored by the same researcher, not blind."}

def save_results(out_dir:Path,runs=RUNS,budget=BUDGET,seed=SEED):
    result=execute(runs,budget,seed)
    out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/"exp003.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return result
