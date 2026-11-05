"""EXP-012 synthetic unit fixtures: never use public answers to tune policy."""
import copy
import json
import unittest

from lab.exp012_calibration import EXPECTED_IDS, grade_rows, score_pinned_source


def fixture():
    responses = [18, 2, 187, 17]
    indices = [13, 37, 59, 81]
    data = json.loads(
        ( __import__("pathlib").Path(__file__).resolve().parents[1] /
          "results" / "exp012-calibration-observations.json"
        ).read_text(encoding="utf-8")
    )
    # Use locally invented synthetic fixtures, NOT official GSM8K data.
    rows = [{"question": "synthetic", "answer": "synthetic\n#### 0"}
            for _ in range(1319)]
    for i, val in zip(indices, responses):
        rows[i]["answer"] = "synthetic\n#### " + str(val)
    return rows, data


class Exp012CalibrationTests(unittest.TestCase):
    def test_four_answers_score_in_synthetic_fixture(self):
        rows, records = fixture()
        report = grade_rows(rows, records)
        self.assertEqual(report["correct"], 4)
        self.assertEqual(report["calibration_cases_total"], 4)
        self.assertFalse(report["model_orchestration_compared"])

    def test_one_wrong_is_retained_in_denominator(self):
        rows, records = fixture()
        records["answers"][1]["output"] = "FINAL: 999"
        report = grade_rows(rows, records)
        self.assertEqual(report["correct"], 3)
        self.assertEqual(report["status_counts"]["incorrect"], 1)
        self.assertEqual(report["calibration_cases_total"], 4)

    def test_invalid_numeric_output_is_distinct(self):
        rows, records = fixture()
        records["answers"][0]["output"] = "Maybe 18"
        report = grade_rows(rows, records)
        self.assertEqual(report["status_counts"]["malformed"], 1)

    def test_unanswered_is_counted(self):
        rows, records = fixture()
        records["answers"][0]["output"] = None
        self.assertEqual(grade_rows(rows, records)["status_counts"]["unanswered"], 1)

    def test_wrong_indices_rejected(self):
        rows, records = fixture()
        records["task_indices_base0"][3] = 103
        with self.assertRaises(ValueError):
            grade_rows(rows, records)

    def test_mutated_order_rejected(self):
        rows, records = fixture()
        records["answers"].reverse()
        with self.assertRaises(ValueError):
            grade_rows(rows, records)

    def test_fake_provenance_rejected(self):
        rows, records = fixture()
        records["provenance_attested"] = True
        with self.assertRaises(ValueError):
            grade_rows(rows, records)

    def test_fake_independence_rejected(self):
        rows, records = fixture()
        records["session_independent"] = True
        with self.assertRaises(ValueError):
            grade_rows(rows, records)

    def test_not_calibration_rejected(self):
        rows, records = fixture()
        records["split"] = "evaluation"
        with self.assertRaises(ValueError):
            grade_rows(rows, records)

    def test_no_gold_exposed_by_report(self):
        rows, records = fixture()
        report = grade_rows(rows, records)
        self.assertEqual([x["task_id"] for x in report["evaluations"]],
                         list(EXPECTED_IDS))
        for x in report["evaluations"]:
            self.assertEqual(set(x), {"task_id", "status"})
        self.assertNotIn("gold", json.dumps(report).lower())
        self.assertFalse(report["independent_holdout_claim"])
        self.assertFalse(report["fresh_contexts_verified"])

    def test_wrong_source_sha_is_rejected_before_scoring(self):
        _, observed = fixture()
        with self.assertRaises(ValueError):
            score_pinned_source(b'{"question":"x","answer":"#### 42"}\n',
                                observed)


if __name__ == "__main__":
    unittest.main()
