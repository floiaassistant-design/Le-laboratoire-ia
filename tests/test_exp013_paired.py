"""EXP-013 synthetic-only tests: no observed model outputs and no API."""
import copy
import hashlib
import json
import unittest

from lab.exp010a_adaptive import POLICIES
from lab.exp011_manual import CALIBRATION, EVALUATION, PLAN, make_packet_data, score
from lab.exp013_paired import analyze, preflight, validate_graded


def fixtures():
    plan_raw = PLAN.read_bytes()
    plan = json.loads(plan_raw)
    rows = []
    for i in range(1319):
        length = 25 if i in (CALIBRATION[0], EVALUATION[0]) else (
            53 if i % 3 == 2 else 44)
        rows.append({
            "question": " ".join(["synthetic"] * length) + " problem?",
            "answer": "Invented test oracle.\n#### 42",
        })
    return make_packet_data(rows, plan, hashlib.sha256(plan_raw).hexdigest())


def index_records(packet, responses):
    tasks = {t["task_id"]: t for t in packet["tasks"]}
    return { (rec["task_id"], rec["policy"]): (
        rec, tasks[rec["task_id"]]["routes"][rec["policy"]])
        for rec in responses["records"]
    }


def complete(rec, route, *, correct=True, approve=True, distinct=True):
    if route == "blocked":
        return
    rec["model_label"] = "SYNTHETIC_ONLY_NOT_REAL_MODEL"
    first = "FINAL: 42" if correct else "FINAL: 41"
    rec["outputs"]["solver"] = first
    rec["sessions"]["solver"] = rec["task_id"] + ":" + rec["policy"] + ":solver"
    if route in ("parallel", "review"):
        role = "independent" if route == "parallel" else "critic"
        rec["outputs"][role] = (
            first if role == "independent" else
            ("VERDICT: APPROVE" if approve else "VERDICT: REJECT")
        )
        rec["sessions"][role] = (
            rec["task_id"] + ":" + rec["policy"] + ":" + role
            if distinct else rec["sessions"]["solver"]
        )


class Exp013PairedAnalysisTests(unittest.TestCase):
    def test_empty_experiment_has_no_accuracy_claim(self):
        p, k, recs = fixtures()
        result = analyze(score(p, k, recs))
        self.assertEqual(result["reported_model_observations_exp011"], 0)
        self.assertFalse(result["experimental_model_comparison_scientifically_proven"])
        self.assertFalse(result["all_evaluation_trials_have_known_operational_outcomes"])
        for policy in POLICIES:
            metric = result["cohorts"]["evaluation"][policy]
            self.assertIsNone(metric["answer_accuracy_when_answered"])
            self.assertFalse(metric["has_scored_model_outputs"])

    def test_synthetic_preflight_is_not_observation(self):
        x = preflight()
        self.assertEqual(x["reported_model_observations_exp011"], 0)
        self.assertEqual(x["phase"], "synthetic_empty_response_preflight_no_models")
        self.assertTrue(x["not_a_real_experimental_result"])

    def test_baseline_missing_pairs_are_not_zero_difference(self):
        p, k, recs = fixtures()
        report = analyze(score(p, k, recs))
        pair = report["adaptive_vs_baselines"]["always_single"]
        self.assertEqual(pair["pairs_with_known_operational_outcomes"], 0)
        self.assertIsNone(pair["delta_success_on_known_pairs"])
        self.assertEqual(pair["delta_success_over_all_tasks_bounds"]["lower"], -1.0)
        self.assertEqual(pair["delta_success_over_all_tasks_bounds"]["upper"], 1.0)

    def test_design_block_is_not_model_error(self):
        p, k, recs = fixtures()
        summary = analyze(score(p, k, recs))
        parallel = summary["cohorts"]["evaluation"]["always_parallel"]
        self.assertGreater(parallel["status_counts"]["blocked_by_design"], 0)
        self.assertEqual(parallel["status_counts"]["incorrect"], 0)
        pair = summary["adaptive_vs_baselines"]["always_parallel"]
        self.assertGreater(pair["baseline_blocked_by_rule"], 0)
        self.assertTrue(pair["structural_policy_constraint_can_explain_difference"])

    def test_partial_answer_coverage_does_not_overstate_accuracy(self):
        p, k, recs = fixtures()
        trial = next(x for x in recs["records"]
                     if x["policy"] == "always_single" and
                     x["task_id"] == "gsm8k-test-" + str(EVALUATION[0]).zfill(4))
        complete(trial, "single")
        result = analyze(score(p, k, recs))
        m = result["cohorts"]["evaluation"]["always_single"]
        self.assertEqual(m["correct_answers"], 1)
        self.assertEqual(m["answer_accuracy_when_answered"], 1.0)
        self.assertEqual(m["answer_coverage_per_assigned_task"], 1 / 12)
        self.assertEqual(m["task_success_fraction_lower_bound"], 1 / 12)
        self.assertEqual(m["task_success_fraction_upper_bound"], 1.0)

    def test_a_known_wrong_answer_is_a_known_failure(self):
        p, k, recs = fixtures()
        r = next(x for x in recs["records"]
                 if x["policy"] == "always_single" and
                 x["task_id"] == "gsm8k-test-" + str(EVALUATION[0]).zfill(4))
        complete(r, "single", correct=False)
        m = analyze(score(p, k, recs))["cohorts"]["evaluation"]["always_single"]
        self.assertEqual(m["status_counts"]["incorrect"], 1)
        self.assertEqual(m["unknown_or_invalid_provenance"], 11)
        self.assertEqual(m["task_success_fraction_upper_bound"], 11 / 12)

    def test_critic_rejection_is_abstention_not_wrong_answer(self):
        p, k, recs = fixtures()
        trial = next(x for x in recs["records"]
                     if x["policy"] == "always_review" and
                     x["task_id"] == "gsm8k-test-" + str(EVALUATION[0]).zfill(4))
        complete(trial, "review", approve=False)
        m = analyze(score(p, k, recs))["cohorts"]["evaluation"]["always_review"]
        self.assertEqual(m["status_counts"]["abstained"], 1)
        self.assertEqual(m["status_counts"]["incorrect"], 0)
        self.assertIsNone(m["answer_accuracy_when_answered"])

    def test_reused_sessions_are_unknown_not_wrong(self):
        p, k, recs = fixtures()
        trial = next(x for x in recs["records"]
                     if x["policy"] == "always_parallel" and
                     x["task_id"] == "gsm8k-test-" + str(EVALUATION[1]).zfill(4))
        complete(trial, "parallel", distinct=False)
        m = analyze(score(p, k, recs))["cohorts"]["evaluation"]["always_parallel"]
        self.assertEqual(m["status_counts"]["nonindependent_sessions"], 1)
        self.assertEqual(m["status_counts"]["incorrect"], 0)

    def test_full_synthetic_roster_produces_paired_counts(self):
        p, k, recs = fixtures()
        for rec, route in index_records(p, recs).values():
            complete(rec, route)
        result = analyze(score(p, k, recs))
        self.assertTrue(result["all_evaluation_trials_have_known_operational_outcomes"])
        self.assertFalse(result["experimental_model_comparison_scientifically_proven"])
        pair = result["adaptive_vs_baselines"]["always_parallel"]
        self.assertEqual(pair["pairs_with_known_operational_outcomes"], 12)
        self.assertGreater(pair["adaptive_correct_while_baseline_blocked"], 0)
        self.assertEqual(pair["baseline_only_correct"], 0)
        self.assertEqual(pair["delta_success_over_all_tasks_bounds"]["lower"],
                         pair["delta_success_over_all_tasks_bounds"]["upper"])
        self.assertEqual(pair["inferential_p_value"], None)

    def test_model_costs_missing_are_null(self):
        p, k, recs = fixtures()
        for rec, route in index_records(p, recs).values():
            complete(rec, route)
        m = analyze(score(p, k, recs))["cohorts"]["evaluation"]["adaptive"]
        metric = m["self_reported_resource_metrics"]["input_tokens"]
        self.assertEqual(metric["reported_trials"], 0)
        self.assertIsNone(metric["total_if_all_reported"])

    def test_complete_token_reporting_is_still_self_reported(self):
        p, k, recs = fixtures()
        for rec, route in index_records(p, recs).values():
            complete(rec, route)
            if route != "blocked":
                rec["input_tokens"] = 11
                rec["output_tokens"] = 7
                rec["elapsed_seconds"] = 1.5
        m = analyze(score(p, k, recs))["cohorts"]["evaluation"]["adaptive"]
        self.assertEqual(
            m["self_reported_resource_metrics"]["input_tokens"]["total_if_all_reported"],
            12 * 11)
        self.assertTrue(m["self_reported_resource_metrics"]["input_tokens"]["self_reported_only"])

    def test_duplicate_pair_rejected(self):
        p, k, recs = fixtures()
        g = score(p, k, recs)
        g["evaluations"][1] = copy.deepcopy(g["evaluations"][0])
        with self.assertRaises(ValueError):
            analyze(g)

    def test_missing_pair_rejected(self):
        p, k, recs = fixtures()
        g = score(p, k, recs)
        g["evaluations"].pop()
        with self.assertRaises(ValueError):
            analyze(g)

    def test_mutated_split_rejected(self):
        p, k, recs = fixtures()
        g = score(p, k, recs)
        g["evaluations"][0]["split"] = "evaluation"
        with self.assertRaises(ValueError):
            analyze(g)

    def test_invalid_status_rejected(self):
        p, k, recs = fixtures()
        g = score(p, k, recs)
        g["evaluations"][0]["status"] = "superior_ai"
        with self.assertRaises(ValueError):
            analyze(g)

    def test_invented_role_calls_rejected(self):
        p, k, recs = fixtures()
        g = score(p, k, recs)
        g["evaluations"][0]["role_calls_self_reported"] = True
        with self.assertRaises(ValueError):
            analyze(g)

    def test_nonfinite_elapsed_metric_rejected(self):
        p, k, recs = fixtures()
        g = score(p, k, recs)
        g["evaluations"][0]["elapsed_seconds_self_reported"] = float("nan")
        with self.assertRaises(ValueError):
            analyze(g)

    def test_wrong_recorded_count_rejected(self):
        p, k, recs = fixtures()
        g = score(p, k, recs)
        g["real_model_results_recorded"] = 64
        with self.assertRaises(ValueError):
            analyze(g)

    def test_no_prompts_or_gold_answers_in_report(self):
        p, k, recs = fixtures()
        g = analyze(score(p, k, recs))
        serialized = json.dumps(g)
        self.assertNotIn("#### 42", serialized)
        self.assertNotIn("QUESTION:", serialized)
        self.assertEqual(g["primary_comparisons"], "evaluation_only")
        self.assertFalse(g["chat_session_independence_attested"])


if __name__ == "__main__":
    unittest.main()
