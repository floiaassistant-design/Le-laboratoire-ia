"""EXP-001, equal query budget: random vs curated boundary tests."""
import json
from pathlib import Path
from random import Random
from .cases import CASES

DEFAULT_SEED=20261102
DEFAULT_RUNS=200
DEFAULT_BUDGET=12

def probes(case, style, rng, budget):
    if style=="uniforme":
        return [case.random_input(rng) for _ in range(budget)]
    if style=="limites":
        targeted=list(case.edge_inputs[:budget])
        return targeted+[case.random_input(rng) for _ in range(budget-len(targeted))]
    raise ValueError(f"Unknown style: {style}")

def detect(case, candidates):
    return any(case.reference(arg)!=case.mutant(arg) for arg in candidates)

def run(runs=DEFAULT_RUNS,budget=DEFAULT_BUDGET,seed=DEFAULT_SEED):
    if runs<1 or budget<1: raise ValueError("runs and budget must be positive")
    rows=[]
    for trial in range(runs):
        for i,case in enumerate(CASES):
            for style in ("uniforme","limites"):
                rng=Random(seed+100_003*trial+37*i+(0 if style=="uniforme" else 1))
                hit=detect(case,probes(case,style,rng,budget))
                rows.append({"run":trial,"case":case.name,"method":style,"detected":int(hit),"budget":budget})
    summary={}
    for style in ("uniforme","limites"):
        sub=[r for r in rows if r["method"]==style]
        count=sum(r["detected"] for r in sub)
        summary[style]={"detected":count,"total":len(sub),"rate":round(count/len(sub),6),
                        "by_case":{case.name:round(sum(r["detected"] for r in sub if r["case"]==case.name)/runs,6) for case in CASES}}
    return rows,{"experiment":"EXP-001","seed":seed,"runs":runs,"budget_per_case":budget,
                 "cases":len(CASES),"summary":summary,
                 "conclusion_scope":"Synthetic boundary mutants; NOT an LLM comparison"}

def save_results(out_dir:Path,runs=DEFAULT_RUNS,budget=DEFAULT_BUDGET,seed=DEFAULT_SEED):
    _,result=run(runs,budget,seed)
    out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/"exp001.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return result
