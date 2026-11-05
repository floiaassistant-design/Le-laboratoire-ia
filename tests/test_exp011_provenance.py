"""EXP-011C provenance checks use fabricated records; no LLM or gold score."""
import copy
import hashlib
import json
import unittest

from lab.exp010a_adaptive import POLICIES
from lab.exp011_manual import CALIBRATION, EVALUATION, PLAN, make_packet_data
from lab.exp011_runbook import make_runbook
from lab.exp011_provenance import audit


def fixture():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    rows = [{"question": " ".join(["small"] * 24) + "?",
             "answer": "Artificial answer\n#### 98765"} for _ in range(1319)]
    rows[CALIBRATION[0]]["question"] = " ".join(["medium"] * 43) + "?"
    rows[EVALUATION[0]]["question"] = " ".join(["long"] * 53) + "?"
    packets, _, responses = make_packet_data(
        rows, plan, hashlib.sha256(PLAN.read_bytes()).hexdigest()
    )
    return packets, make_runbook(packets), responses


def populate(book, responses, trial, reference, label="GPT-6"):
    rec = next(r for r in responses["records"] if
               (r["task_id"], r["policy"]) == (trial["task_id"], trial["policy"]))
    rec["model_label"] = label
    for index, step in enumerate(trial["steps"]):
        role = step["role"]
        rec["outputs"][role] = (
            "VERDICT: APPROVE" if role == "critic" else "FINAL: 12"
        )
        rec["sessions"][role] = reference + "-" + str(index)
    return rec


class ProvenanceAuditTests(unittest.TestCase):
    def test_empty_template_keeps_full_denominator_without_model_claims(self):
        packets, book, responses = fixture()
        report = audit(packets, book, responses)
        self.assertEqual(report["planned_trials"], 64)
        self.assertEqual(len(report["trials"]), 64)
        self.assertEqual(report["model_calls_performed_by_audit"], 0)
        self.assertFalse(report["independence_verified"])
        self.assertFalse(report["quality_or_accuracy_evaluated"])
        self.assertFalse(report["chronological_order_verified"])
        self.assertEqual(report["duplicated_session_references_count"], 0)
        for item in report["summary"]:
            self.assertEqual(item["trials_total"],
                             4 if item["split"] == "calibration" else 12)
            self.assertEqual(item["roles_reported"], 0)
        self.assertNotIn("98765", json.dumps(report))

    def test_two_distinct_complete_trials_are_only_self_reported(self):
        packets, book, responses = fixture()
        trials = [t for t in book["trials"] if t["steps"]][:2]
        for n, trial in enumerate(trials):
            populate(book, responses, trial, "unique-" + str(n))
        report = audit(packets, book, responses)
        complete = [t for t in report["trials"]
                    if t["status"] == "complete_self_reported"]
        self.assertEqual(len(complete), 2)
        self.assertFalse(report["independence_verified"])
        self.assertEqual(report["trials_affected_by_reuse"], 0)

    def test_reused_chat_across_different_trials_is_detected(self):
        packets, book, responses = fixture()
        trials = [t for t in book["trials"] if t["steps"]][:2]
        for t in trials:
            populate(book, responses, t, "same-ref")
        report = audit(packets, book, responses)
        self.assertGreaterEqual(report["duplicated_session_references_count"], 1)
        self.assertEqual(report["trials_affected_by_reuse"], 2)
        self.assertEqual(sum(t["status"] == "reused_session_reference"
                             for t in report["trials"]), 2)
        self.assertNotIn("same-ref", json.dumps(report))

    def test_one_trial_reuses_context_for_two_roles(self):
        packets, book, responses = fixture()
        trial = next(t for t in book["trials"] if len(t["steps"]) == 2)
        record = populate(book, responses, trial, "separate")
        roles = [step["role"] for step in trial["steps"]]
        record["sessions"][roles[1]] = record["sessions"][roles[0]]
        report = audit(packets, book, responses)
        self.assertEqual(report["trials_affected_by_reuse"], 1)
        self.assertTrue(next(t for t in report["trials"]
                             if t["trial_id"] == trial["trial_id"])
                        ["has_reused_session_reference"])

    def test_partials_and_missing_model_provenance_are_separate(self):
        packets, book, responses = fixture()
        trial = next(t for t in book["trials"] if len(t["steps"]) == 2)
        record = populate(book, responses, trial, "distinct")
        role = trial["steps"][1]["role"]
        record["outputs"][role] = None
        record["sessions"][role] = None
        report = audit(packets, book, responses)
        self.assertEqual(next(t for t in report["trials"]
                              if t["trial_id"] == trial["trial_id"])["status"],
                         "partial")
        record["outputs"][role] = "VERDICT: APPROVE" if role == "critic" else "FINAL: 12"
        record["sessions"][role] = "distinct-new"
        record["model_label"] = None
        report = audit(packets, book, responses)
        self.assertEqual(next(t for t in report["trials"]
                              if t["trial_id"] == trial["trial_id"])["status"],
                         "missing_model_label")

    def test_mixed_models_are_a_warning_not_claim_of_model_identity(self):
        packets, book, responses = fixture()
        trials = [t for t in book["trials"] if t["steps"]][:2]
        populate(book, responses, trials[0], "m1", "model-a")
        populate(book, responses, trials[1], "m2", "model-b")
        report = audit(packets, book, responses)
        self.assertTrue(report["mixed_model_label_warning"])
        self.assertFalse(report["same_model_verified"])

    def test_blocked_route_rejects_fabricated_role_call(self):
        packets, book, responses = fixture()
        trial = next(t for t in book["trials"] if not t["steps"])
        record = next(r for r in responses["records"] if
                      (r["task_id"], r["policy"]) ==
                      (trial["task_id"], trial["policy"]))
        record["outputs"]["solver"] = "FINAL: 12"
        record["sessions"]["solver"] = "chat-1"
        with self.assertRaises(ValueError):
            audit(packets, book, responses)

    def test_rejects_orphaned_output_and_untrusted_record(self):
        packets, book, responses = fixture()
        record = responses["records"][0]
        record["outputs"]["solver"] = "FINAL: 12"
        with self.assertRaises(ValueError):
            audit(packets, book, responses)
        record["outputs"]["solver"] = None
        record["input_tokens"] = True
        with self.assertRaises(ValueError):
            audit(packets, book, responses)

    def test_rejects_duplicate_records_and_tampered_runbook(self):
        packets, book, responses = fixture()
        responses["records"][1] = copy.deepcopy(responses["records"][0])
        with self.assertRaises(ValueError):
            audit(packets, book, responses)
        _, book, responses = fixture()
        book["trials"][0]["route"] = "parallel"
        with self.assertRaises(ValueError):
            audit(packets, book, responses)

    def test_metric_coverage_reports_null_as_unknown_not_zero(self):
        packets, book, responses = fixture()
        trial = next(t for t in book["trials"] if t["steps"])
        record = populate(book, responses, trial, "metric")
        record["elapsed_seconds"] = 0
        record["input_tokens"] = None
        report = audit(packets, book, responses)
        item = next(t for t in report["trials"]
                    if t["trial_id"] == trial["trial_id"])
        self.assertEqual(item["metrics_reported"],
                         {"elapsed_seconds": True,
                          "input_tokens": False, "output_tokens": False})


if __name__ == "__main__":
    unittest.main()
