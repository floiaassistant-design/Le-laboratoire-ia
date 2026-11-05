"""Offline tests of EXP-011B's manual scheduling; no model calls."""
import copy
import hashlib
import json
import unittest

from lab.exp010a_adaptive import POLICIES
from lab.exp011_manual import CALIBRATION, EVALUATION, PLAN, make_packet_data
from lab.exp011_runbook import SOLVER_PLACEHOLDER, make_runbook


def fixture():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    # Synthetic-only questions; answer is intentionally not put in packets.
    rows = [{"question": " ".join(["short"] * 24) + "?",
             "answer": "Artificial solution.\\n#### 98765"}
            for _ in range(1319)]
    rows[CALIBRATION[0]]["question"] = " ".join(["middle"] * 43) + "?"
    rows[EVALUATION[0]]["question"] = " ".join(["long"] * 52) + "?"
    packets, key, responses = make_packet_data(
        rows, plan, hashlib.sha256(PLAN.read_bytes()).hexdigest())
    return packets, key, responses


class ManualRunbookTests(unittest.TestCase):
    def test_balanced_policy_positions_in_each_split(self):
        packets, _, _ = fixture()
        book = make_runbook(packets)
        self.assertEqual(book["total_trials_planned"], 64)
        for split, count in (("calibration", 1), ("evaluation", 3)):
            for pos in book["policy_order_counts"][split].values():
                self.assertEqual(pos, {p: count for p in POLICIES})

    def test_only_question_context_never_answer_key(self):
        packets, _, _ = fixture()
        payload = json.dumps(make_runbook(packets))
        self.assertNotIn("98765", payload)
        self.assertNotIn("####", payload)
        self.assertFalse(make_runbook(packets)["gold_answers_included"])

    def test_role_templates_and_separated_context_slots(self):
        book = make_runbook(fixture()[0])
        steps = [s for trial in book["trials"] for s in trial["steps"]]
        aliases = [s["planned_context_slot"] for s in steps]
        self.assertEqual(len(aliases), len(set(aliases)))
        self.assertTrue(all(s["requires_fresh_chat"] for s in steps))
        self.assertTrue(all("QUESTION:" in s["prompt_template"] for s in steps))
        self.assertTrue(all(SOLVER_PLACEHOLDER in s["prompt_template"]
                            for s in steps if s["role"] == "critic"))
        self.assertTrue(all(SOLVER_PLACEHOLDER not in s["prompt_template"]
                            for s in steps if s["role"] != "critic"))

    def test_blocked_parallel_has_zero_calls(self):
        book = make_runbook(fixture()[0])
        blocked = [x for x in book["trials"]
                   if x["policy"] == "always_parallel" and
                   x["task_id"] == "gsm8k-test-" + str(EVALUATION[1]).zfill(4)]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(blocked[0]["route"], "blocked")
        self.assertEqual(blocked[0]["role_calls_planned"], 0)
        self.assertEqual(blocked[0]["steps"], [])

    def test_routes_unchanged_for_short_medium_long(self):
        book = make_runbook(fixture()[0])
        chosen = {x["task_id"]: x["route"] for x in book["trials"]
                  if x["policy"] == "adaptive"}
        self.assertEqual(chosen["gsm8k-test-" + str(CALIBRATION[0]).zfill(4)], "parallel")
        self.assertEqual(chosen["gsm8k-test-" + str(EVALUATION[0]).zfill(4)], "review")
        self.assertEqual(chosen["gsm8k-test-" + str(EVALUATION[1]).zfill(4)], "single")

    def test_no_model_execution_claim_and_determinism(self):
        packets, _, _ = fixture()
        first = make_runbook(packets)
        self.assertEqual(first, make_runbook(packets))
        self.assertTrue(first["no_real_model_evaluation"])
        self.assertFalse(first["sessions_independent_verified"])
        self.assertEqual(first["model_calls_executed"], 0)
        self.assertEqual(first["role_calls_planned"],
                         sum(t["role_calls_planned"] for t in first["trials"]))

    def test_tampered_route_is_refused(self):
        packets, _, _ = fixture()
        packets["tasks"][0]["routes"]["adaptive"] = "single"
        with self.assertRaises(ValueError):
            make_runbook(packets)

    def test_tampered_input_word_count_is_refused(self):
        packets, _, _ = fixture()
        packets["tasks"][0]["input_word_count"] = 999
        with self.assertRaises(ValueError):
            make_runbook(packets)

    def test_tampered_source_fingerprint_is_refused(self):
        packets, _, _ = fixture()
        packets["source_blob_sha"] = "wrong-sha"
        with self.assertRaises(ValueError):
            make_runbook(packets)

    def test_missing_task_is_refused(self):
        packets, _, _ = fixture()
        packets["tasks"].pop()
        with self.assertRaises(ValueError):
            make_runbook(packets)

    def test_calibration_precedes_evaluation(self):
        book = make_runbook(fixture()[0])
        splits = [t["split"] for t in book["trials"]]
        self.assertEqual(splits[:16], ["calibration"] * 16)
        self.assertEqual(splits[16:], ["evaluation"] * 48)


if __name__ == "__main__":
    unittest.main()
