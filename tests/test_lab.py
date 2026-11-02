import unittest
from random import Random
from lab.cases import CASES
from lab.experiment import run as run_exp1,probes as baseline_probes
from lab.robustness import run as run_exp1b
from lab.hybrid import training_cases,HOLDOUT,execute,probes,evaluate

class LaboratoryTests(unittest.TestCase):
    def test_baseline_reproducibility(self):
        self.assertEqual(run_exp1(runs=2),run_exp1(runs=2))
        self.assertEqual(run_exp1b(runs=2),run_exp1b(runs=2))
    def test_hybrid_reproducibility(self):
        self.assertEqual(execute(runs=2),execute(runs=2))
    def test_equal_test_budget(self):
        for case in (*training_cases(),*HOLDOUT):
            for n in (0,3,6,9,12):
                self.assertEqual(len(probes(case,n,Random(4),12)),12)
    def test_baseline_budget(self):
        for c in CASES:
            for method in ("uniforme","limites"):
                self.assertEqual(len(baseline_probes(c,method,Random(3),12)),12)
    def test_invalid_allocation(self):
        with self.assertRaises(ValueError):probes(HOLDOUT[0],13,Random(0))
        with self.assertRaises(ValueError):evaluate(HOLDOUT,allocations=(-1,))
    def test_holdout_coverage(self):
        for c in HOLDOUT:
            self.assertTrue(any(c.reference(x)!=c.mutant(x) for x in range(-100,5002)),c.name)
    def test_cases_separate(self):
        self.assertFalse({c.name for c in training_cases()} & {c.name for c in HOLDOUT})
    def test_predeclared_mix_selection(self):
        r=execute(runs=10)
        self.assertIn(r["selected_edges"],(0,3,6,9,12))
        self.assertEqual(r["holdout_cases"],6)
    def test_invalid_budget(self):
        with self.assertRaises(ValueError):run_exp1(budget=0)
        with self.assertRaises(ValueError):run_exp1b(budget=0)
    def test_boundary_mutants_detectable(self):
        for c in CASES:
            self.assertTrue(any(c.reference(x)!=c.mutant(x) for x in c.edge_inputs),c.name)

if __name__=="__main__":unittest.main()
