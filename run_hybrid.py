"""Reproduce EXP-003, offline. No API access or external dependencies."""
from pathlib import Path
from lab.hybrid import save_results
if __name__=="__main__":
    report=save_results(Path(__file__).parent/"results")
    print("Known training:",{k:v["rate"] for k,v in report["training"].items()})
    print("Selected edge allocation:",report["selected_edges"],"/12")
    print("Holdout:",{k:v["rate"] for k,v in report["holdout"].items()})
    print(report["note"])
