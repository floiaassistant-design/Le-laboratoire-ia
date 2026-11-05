"""EXP-011D guide tests use fabricated GSM8K-shaped input and outputs only."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from lab.exp011_manual import CALIBRATION, EVALUATION, PLAN, make_packet_data
from lab.exp011_provenance import audit
from lab.exp011_runbook import SOLVER_PLACEHOLDER, make_runbook
from lab.exp011_session_guide import atomic_write, next_step, progress, record_step


def fixture(words=43):
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    rows = [
        {"question": " ".join(["fictitious"] * 24) + "?",
         "answer": "Not a real model observation\n#### 98765"}
        for _ in range(1319)
    ]
    rows[CALIBRATION[0]]["question"] = " ".join(["q"] * words) + "?"
    packets, _, responses = make_packet_data(
        rows, plan, hashlib.sha256(PLAN.read_bytes()).hexdigest()
    )
    return packets, make_runbook(packets), responses


def record_next(packets, book, responses, n, model="GPT-6", output=None):
    step = next_step(book, responses, packets)
    if step is None:
        raise AssertionError("Unexpected end of roster")
    text = (output if output is not None else
            "VERDICT: REJECT" if step["role"] == "critic" else "FINAL: 9")
    return record_step(
        packets, book, responses,
        task_id=step["task_id"], policy=step["policy"], role=step["role"],
        session=f"new-chat-{n}", model=model, output=text,
    )


class GuidedCollectionTests(unittest.TestCase):
    def test_initial_next_only_shows_question_and_never_key(self):
        packets, book, responses = fixture()
        step = next_step(book, responses, packets)
        self.assertEqual(step["split"], "calibration")
        self.assertEqual(step["role"], "solver")
        self.assertEqual(step["policy"], "adaptive")
        self.assertNotIn("98765", json.dumps(step))
        self.assertNotIn("####", json.dumps(step))
        self.assertTrue(step["fresh_chat_required"])
        self.assertTrue(step["no_chat_opened_or_model_called"])

    def test_parallel_second_role_never_sees_first_model_output(self):
        packets, book, responses = fixture(words=43)
        responses = record_next(packets, book, responses, 1, output="FINAL: 876543")
        step = next_step(book, responses, packets)
        self.assertEqual(step["role"], "independent")
        self.assertNotIn("876543", step["prompt"])
        self.assertNotIn(SOLVER_PLACEHOLDER, step["prompt"])

    def test_critic_receives_only_manually_reported_solver_final(self):
        packets, book, responses = fixture(words=53)
        responses = record_next(packets, book, responses, 1, output="FINAL: 876543")
        step = next_step(book, responses, packets)
        self.assertEqual(step["role"], "critic")
        self.assertIn("FINAL: 876543", step["prompt"])
        self.assertNotIn(SOLVER_PLACEHOLDER, step["prompt"])
        self.assertNotIn("98765", step["prompt"])

    def test_duplicate_chat_ref_is_rejected_without_mutating_template(self):
        packets, book, responses = fixture()
        first = record_next(packets, book, responses, 1)
        snapshot = copy.deepcopy(first)
        step = next_step(book, first, packets)
        with self.assertRaisesRegex(ValueError, "already used"):
            record_step(
                packets, book, first,
                task_id=step["task_id"], policy=step["policy"], role=step["role"],
                output="FINAL: 99", session="new-chat-1", model="GPT-6",
            )
        self.assertEqual(first, snapshot)
        self.assertIsNone(responses["records"][0]["outputs"]["solver"])

    def test_order_cannot_be_skipped_or_record_replaced(self):
        packets, book, responses = fixture()
        next_one = next_step(book, responses, packets)
        with self.assertRaisesRegex(ValueError, "Out of order"):
            record_step(
                packets, book, responses,
                task_id=next_one["task_id"], policy=next_one["policy"],
                role="critic", output="VERDICT: APPROVE",
                session="chat-wrong", model="GPT-6",
            )
        updated = record_next(packets, book, responses, 1)
        with self.assertRaisesRegex(ValueError, "Out of order"):
            record_step(
                packets, book, updated,
                task_id=next_one["task_id"], policy=next_one["policy"],
                role=next_one["role"], output="FINAL: 123",
                session="chat-new", model="GPT-6",
            )

    def test_prevent_mixed_model_labels_but_allow_same_label(self):
        packets, book, responses = fixture()
        updated = record_next(packets, book, responses, 1)
        with self.assertRaisesRegex(ValueError, "different model"):
            record_next(packets, book, updated, 2, model="different-model")
        updated = record_next(packets, book, updated, 2, model="GPT-6")
        self.assertEqual(audit(packets, book, updated)["duplicated_session_references_count"], 0)

    def test_missing_metrics_stay_null_and_totals_only_on_last_role(self):
        packets, book, responses = fixture(words=43)
        first = next_step(book, responses, packets)
        with self.assertRaisesRegex(ValueError, "last role"):
            record_step(
                packets, book, responses,
                task_id=first["task_id"], policy=first["policy"],
                role=first["role"], session="chat-1", model="GPT-6",
                output="FINAL: 1", elapsed_seconds=4.2,
            )
        updated = record_next(packets, book, responses, 1)
        second = next_step(book, updated, packets)
        updated = record_step(
            packets, book, updated,
            task_id=second["task_id"], policy=second["policy"],
            role=second["role"], session="chat-2", model="GPT-6",
            output="FINAL: 1", elapsed_seconds=5.0,
        )
        rec = next(r for r in updated["records"]
                   if (r["task_id"], r["policy"]) ==
                   (first["task_id"], first["policy"]))
        self.assertEqual(rec["elapsed_seconds"], 5.0)
        self.assertIsNone(rec["input_tokens"])
        self.assertIsNone(rec["output_tokens"])

    def test_malformed_outputs_are_preserved_not_silently_discarded(self):
        packets, book, responses = fixture(words=24)
        updated = record_next(packets, book, responses, 1, output="nonsense")
        self.assertEqual(updated["records"][0]["outputs"]["solver"], "nonsense")
        self.assertEqual(next_step(book, updated, packets)["role"], "solver")

    def test_blocked_trials_count_and_zero_calls_preserved(self):
        packets, book, responses = fixture(words=24)
        summary = progress(book, responses, packets)
        self.assertEqual(summary["total_planned_trials"], 64)
        self.assertEqual(summary["by_split"]["calibration"]["trials"], 16)
        self.assertEqual(summary["by_split"]["evaluation"]["trials"], 48)
        self.assertGreater(summary["by_split"]["calibration"]["blocked"], 0)
        self.assertEqual(summary["by_split"]["calibration"]["roles_reported"], 0)
        self.assertFalse(summary["session_isolation_verified"])
        self.assertNotIn("98765", json.dumps(summary))

    def test_refuses_runbook_tampering_and_malformed_observations(self):
        packets, book, responses = fixture(words=53)
        tampered = copy.deepcopy(book)
        tampered["trials"][0]["steps"][0]["prompt_template"] += " GOLD: 98765"
        with self.assertRaises(ValueError):
            next_step(tampered, responses, packets)
        step = next_step(book, responses, packets)
        with self.assertRaises(ValueError):
            record_step(
                packets, book, responses,
                task_id=step["task_id"], policy=step["policy"],
                role=step["role"], session="ok-1", model="GPT-6",
                output="X" * 201,
            )

    def test_atomic_write_protects_original_and_preserves_content(self):
        packets, book, responses = fixture()
        new_content = record_next(packets, book, responses, 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "responses.json"
            path.write_text(json.dumps(responses), encoding="utf-8")
            atomic_write(path, new_content)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), new_content)
            self.assertEqual(list(Path(directory).glob(".exp011d-*.tmp")), [])

    def test_all_roles_can_be_recorded_without_touching_oracle(self):
        packets, book, responses = fixture(words=53)
        total_steps = sum(len(trial["steps"]) for trial in book["trials"])
        for n in range(total_steps):
            responses = record_next(packets, book, responses, n)
        self.assertIsNone(next_step(book, responses, packets))
        status = progress(book, responses, packets)
        self.assertIsNone(status["next"])
        self.assertEqual(
            sum(x["complete_self_reported"] + x["blocked"]
                for x in status["by_split"].values()), 64
        )
        self.assertFalse(status["session_isolation_verified"])
        self.assertNotIn("98765", json.dumps(status))


if __name__ == "__main__":
    unittest.main()
