"""EXP-001B, alternate non-boundary mutants."""
import json
from pathlib import Path
from random import Random
from .cases import CASES,Case,leap_year,can_withdraw,is_prime
from .experiment import detect,probes,DEFAULT_BUDGET,DEFAULT_RUNS,DEFAULT_SEED

def shipping_other_error(n): return False if 7000<=n<8000 else (n>=5000)
def password_other_error(n): return False if 30<=n<=40 else (8<=n<=64)
def leap_other_error(n): return not leap_year(n) if 2012<=n<=2020 else leap_year(n)
def prime_other_error(n): return False if 100<=n<=400 else is_prime(n)
def withdrawal_other_error(arg):
    balance,amount=arg
    return False if 250<=amount<=300 and balance>=amount else can_withdraw(arg)

OTHER_MUTANTS={
    "annee_bissextile":leap_other_error,"retrait_bancaire":withdrawal_other_error,
    "livraison_gratuite":shipping_other_error,"mot_de_passe":password_other_error,
    "nombre_premier":prime_other_error,
}

def run(runs=DEFAULT_RUNS,budget=DEFAULT_BUDGET,seed=DEFAULT_SEED):
    if runs<1 or budget<1: raise ValueError("runs and budget must be positive")
    rows=[]
    for trial in range(runs):
        for i,case in enumerate(CASES):
            if case.name not in OTHER_MUTANTS: continue
            other=Case(case.name,case.description,case.reference,OTHER_MUTANTS[case.name],case.random_input,case.edge_inputs)
            for style in ("uniforme","limites"):
                rng=Random(seed+100_003*trial+37*i+(0 if style=="uniforme" else 1))
                rows.append({"run":trial,"case":case.name,"method":style,
                             "detected":int(detect(other,probes(other,style,rng,budget))),"budget":budget})
    result={"experiment":"EXP-001B","runs":runs,"budget_per_case":budget,
            "seed":seed,"cases":len(OTHER_MUTANTS),"summary":{}}
    for style in ("uniforme","limites"):
        sub=[r for r in rows if r["method"]==style]
        count=sum(r["detected"] for r in sub)
        result["summary"][style]={"detected":count,"total":len(sub),
            "rate":round(count/len(sub),6),
            "by_case":{name:round(sum(r["detected"] for r in sub if r["case"]==name)/runs,6) for name in OTHER_MUTANTS}}
    return rows,result

def save_results(out_dir:Path,runs=DEFAULT_RUNS,budget=DEFAULT_BUDGET,seed=DEFAULT_SEED):
    _,result=run(runs,budget,seed)
    out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/"exp001b.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return result
