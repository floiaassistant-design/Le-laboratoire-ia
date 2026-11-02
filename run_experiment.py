"""Reproduce EXP-001 baseline, offline."""
from pathlib import Path
from lab.experiment import save_results
if __name__=="__main__":
    report=save_results(Path(__file__).parent/"results")
    print({k:(v["detected"],v["total"]) for k,v in report["summary"].items()})
