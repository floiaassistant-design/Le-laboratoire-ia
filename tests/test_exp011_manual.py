"""Offline fixtures for EXP-011: no public tasks executed by models."""
import copy
import hashlib
import json
import unittest

from lab.exp011_manual import (
    CALIBRATION, EVALUATION, PLAN, SOURCE_BLOB, git_blob_sha,
    make_packet_data, normalized_number, read_pinned_source,
    score, task_profile, validate_plan,
)


def plan():
    return json.loads(PLAN.read_text(encoding="utf-8"))


def fixtures():
    p = plan()
    rows = [{"question": " ".join(["Synthetic"] * 44) + " answer?",
             "answer": "Compute a solution.\n#### 42"} for _ in range(1319)]
    return make_packet_data(rows, p, hashlib.sha256(PLAN.read_bytes()).hexdigest())


def fill(rec, outputs, sessions, label="SAME_MODEL"):
    rec["outputs"].update(outputs)
    rec["sessions"].update(sessions)
    rec["model_label"] = label


class PreregisteredManualTrialTests(unittest.TestCase):
    def test_plan_is_predeclared(self):
        validate_plan(plan())

    def test_plan_cannot_relabel_as_independent(self):
        data = plan()
        data["benchmark_limits"]["independent_holdout_claim"] = True
        with self.assertRaises(ValueError):
            validate_plan(data)

    def test_plan_cannot_change_indices(self):
        data = plan()
        data["evaluation_indices"][0] = 0
        with self.assertRaises(ValueError):
            validate_plan(data)

    def test_git_blob_has_deterministic_sha(self):
        payload = b"public fixture\n"
        direct = hashlib.sha1(b"blob 15\0" + payload).hexdigest()
        self.assertEqual(git_blob_sha(payload), direct)

    def test_wrong_dataset_sha_rejected(self):
        with self.assertRaises(ValueError):
            read_pinned_source(b'{"question":"x","answer":"#### 2"}\n', plan())

    def test_exact_row_count_required(self):
        with self.assertRaises(ValueError):
            make_packet_data([], plan(), "f" * 64)

    def test_only_fixed_indices_selected(self):
        packets, key, rec = fixtures()
        indices = [x["row_index"] for x in packets["tasks"]]
        self.assertEqual(indices, list(CALIBRATION) + list(EVALUATION))

    def test_two_splits_have_disjoint_ids(self):
        p, k, r = fixtures()
        self.assertEqual(len({x["task_id"] for x in p["tasks"]}), 16)

    def test_question_bundle_contains_no_answer(self):
        p, key, rec = fixtures()
        text = json.dumps(p, sort_keys=True)
        self.assertNotIn("#### 42", text)
        self.assertNotIn('"answers":', text)
        self.assertFalse(p["model_answers_included"])

    def test_separate_key_has_all_16_answers(self):
        p, key, rec = fixtures()
        self.assertEqual(len(key["answers"]), 16)
        self.assertEqual(set(key["answers"].values()), {"42"})

    def test_64_unfilled_trials(self):
        p, key, records = fixtures()
        self.assertEqual(len(records["records"]), 64)
        self.assertTrue(all(not any(x["outputs"].values()) for x in records["records"]))

    def test_character_counts_choose_simple(self):
        t = task_profile("a " * 39, "simple")
        self.assertFalse(t.parallelizable)
        self.assertEqual(t.uncertainty, 0)

    def test_word_threshold_40_enables_parallel(self):
        t = task_profile("a " * 40, "parallel")
        self.assertTrue(t.parallelizable)
        self.assertEqual(t.uncertainty, 0)

    def test_word_threshold_65_enables_review(self):
        t = task_profile("a " * 65, "review")
        self.assertTrue(t.parallelizable)
        self.assertEqual(t.uncertainty, 2)

    def test_default_template_scores_no_observations(self):
        p, key, records = fixtures()
        report = score(p, key, records)
        self.assertEqual(report["real_model_results_recorded"], 0)
        self.assertTrue(all(s["observed_accuracy"] is None for s in report["summary"]))
        self.assertEqual(len(report["evaluations"]), 64)

    def test_correct_solver_answer_is_recorded(self):
        p, key, recs = fixtures()
        r = next(r for r in recs["records"] if r["policy"] == "always_single")
        fill(r, {"solver": "FINAL: 42"}, {"solver": "session-a"})
        report = score(p, key, recs)
        row = next(x for x in report["evaluations"] if
                   x["task_id"] == r["task_id"] and x["policy"] == r["policy"])
        self.assertEqual(row["status"], "correct")

    def test_incorrect_solver_answer_is_recorded(self):
        p, key, recs = fixtures()
        r = next(r for r in recs["records"] if r["policy"] == "always_single")
        fill(r, {"solver": "FINAL: 41"}, {"solver": "session-a"})
        outcomes = score(p, key, recs)["evaluations"]
        self.assertTrue(any(x["status"] == "incorrect" for x in outcomes))

    def test_parallel_matching_correct_answers(self):
        p, key, recs = fixtures()
        r = next(x for x in recs["records"] if x["policy"] == "always_parallel")
        fill(r, {"solver": "FINAL: 42", "independent": "FINAL: 42.0"},
             {"solver": "chat-a", "independent": "chat-b"})
        outcomes = score(p, key, recs)["evaluations"]
        self.assertTrue(any(x["status"] == "correct" and
                            x["policy"] == "always_parallel" for x in outcomes))

    def test_parallel_disagreement_is_abstention(self):
        p, key, recs = fixtures()
        r = next(x for x in recs["records"] if x["policy"] == "always_parallel")
        fill(r, {"solver": "FINAL: 41", "independent": "FINAL: 42"},
             {"solver": "chat-a", "independent": "chat-b"})
        self.assertTrue(any(x["status"] == "abstained" and
                            x["policy"] == "always_parallel" for x in
                            score(p, key, recs)["evaluations"]))

    def test_critic_approval_can_be_wrong(self):
        p, key, recs = fixtures()
        r = next(x for x in recs["records"] if x["policy"] == "always_review")
        fill(r, {"solver": "FINAL: 41", "critic": "VERDICT: APPROVE"},
             {"solver": "chat-a", "critic": "chat-b"})
        self.assertTrue(any(x["status"] == "incorrect" and
                            x["policy"] == "always_review" for x in
                            score(p, key, recs)["evaluations"]))

    def test_critic_rejection_is_abstention(self):
        p, key, recs = fixtures()
        r = next(x for x in recs["records"] if x["policy"] == "always_review")
        fill(r, {"solver": "FINAL: 42", "critic": "VERDICT: REJECT"},
             {"solver": "chat-a", "critic": "chat-b"})
        self.assertTrue(any(x["status"] == "abstained" and
                            x["policy"] == "always_review" for x in
                            score(p, key, recs)["evaluations"]))

    def test_reused_chat_is_not_independent(self):
        p, key, recs = fixtures()
        r = next(x for x in recs["records"] if x["policy"] == "always_parallel")
        fill(r, {"solver": "FINAL: 42", "independent": "FINAL: 42"},
             {"solver": "same-chat", "independent": "same-chat"})
        self.assertTrue(any(x["status"] == "nonindependent_sessions" for x in
                            score(p, key, recs)["evaluations"]))

    def test_absent_model_provenance_is_not_scored(self):
        p, key, recs = fixtures()
        r = next(x for x in recs["records"] if x["policy"] == "always_single")
        fill(r, {"solver": "FINAL: 42"}, {"solver": "chat-a"}, label=None)
        self.assertTrue(any(x["status"] == "missing_model_provenance"
                            for x in score(p, key, recs)["evaluations"]))

    def test_partial_two_role_trial_is_not_scored(self):
        p, key, recs = fixtures()
        r = next(x for x in recs["records"] if x["policy"] == "always_parallel")
        fill(r, {"solver": "FINAL: 42"}, {"solver": "chat-a"})
        self.assertTrue(any(x["status"] == "unobserved_or_incomplete" and
                            x["role_calls_self_reported"] == 1
                            for x in score(p, key, recs)["evaluations"]))

    def test_unexpected_critic_on_single_is_invalid(self):
        p, key, recs = fixtures()
        r = next(x for x in recs["records"] if x["policy"] == "always_single")
        fill(r, {"critic": "VERDICT: APPROVE"}, {"critic": "chat-extra"})
        with self.assertRaises(ValueError):
            score(p, key, recs)

    def test_duplicate_trial_id_is_rejected(self):
        p, key, recs = fixtures()
        recs["records"][1] = copy.deepcopy(recs["records"][0])
        with self.assertRaises(ValueError):
            score(p, key, recs)

    def test_missing_trial_id_is_rejected(self):
        p, key, recs = fixtures()
        recs["records"].pop()
        with self.assertRaises(ValueError):
            score(p, key, recs)

    def test_different_plan_fingerprint_is_rejected(self):
        p, key, recs = fixtures()
        key["plan_sha256"] = "not-the-real-plan"
        with self.assertRaises(ValueError):
            score(p, key, recs)

    def test_gold_key_requires_all_cases(self):
        p, key, recs = fixtures()
        key["answers"].pop(next(iter(key["answers"])))
        with self.assertRaises(ValueError):
            score(p, key, recs)

    def test_invalid_numeric_format_is_rejected(self):
        with self.assertRaises(ValueError):
            normalized_number("FINAL: forty-two")
        self.assertEqual(normalized_number("FINAL: 1,234.00"), "1234")

    def test_unparseable_model_response_is_separate_status(self):
        p, key, recs = fixtures()
        r = next(x for x in recs["records"] if x["policy"] == "always_single")
        fill(r, {"solver": "maybe 42"}, {"solver": "chat-a"})
        self.assertTrue(any(x["status"] == "malformed_response" for x in
                            score(p, key, recs)["evaluations"]))

    def test_metric_missing_does_not_become_zero(self):
        p, key, recs = fixtures()
        r = next(x for x in recs["records"] if x["policy"] == "always_single")
        fill(r, {"solver": "FINAL: 42"}, {"solver": "chat-a"})
        self.assertTrue(all(s["elapsed_seconds_total"] is None for s in
                            score(p, key, recs)["summary"]))

    def test_invalid_token_metric_fails(self):
        p, key, recs = fixtures()
        recs["records"][0]["input_tokens"] = True
        with self.assertRaises(ValueError):
            score(p, key, recs)

    def test_model_label_mixture_is_reported(self):
        p, key, recs = fixtures()
        two = [r for r in recs["records"] if r["policy"] == "always_single"][:2]
        fill(two[0], {"solver": "FINAL: 42"}, {"solver": "chat-1"}, "model-a")
        fill(two[1], {"solver": "FINAL: 42"}, {"solver": "chat-2"}, "model-b")
        result = score(p, key, recs)
        self.assertTrue(result["mixed_model_label_warning"])


if __name__ == "__main__":
    unittest.main()
