"""EXP-009E: offline/no-network synthetic AST and oracle-hypothesis tests."""
import base64
import copy
import json
import unittest
from unittest.mock import patch

from lab.exp009e_testbank import (
    CANDIDATES, HYPOTHESES, collect_definitions, inspect_case,
    inspect_project, validate_semantics,
)


def plans():
    return (json.loads(HYPOTHESES.read_text(encoding="utf-8")),
            json.loads(CANDIDATES.read_text(encoding="utf-8")))


def source(path="tests/test_sample.py", text="def test_known(): assert True"):
    raw = text.encode("utf-8")
    return {"type": "file", "path": path, "size": len(raw),
            "sha": "a" * 40, "encoding": "base64",
            "content": base64.b64encode(raw).decode("ascii")}


class StaticWitnessTests(unittest.TestCase):
    def test_all_twelve_cases_are_hypotheses_only(self):
        manifest, candidate = plans()
        self.assertEqual(validate_semantics(manifest, candidate),
                         {"cases": 12, "scores": 0, "executed": 0})

    def test_cannot_change_seed_after_freeze(self):
        x, y = plans()
        x["seed"] = 2026
        with self.assertRaises(ValueError):
            validate_semantics(x, y)

    def test_cannot_change_candidate_identity(self):
        x, y = plans()
        x["cases"][0]["id"] = "unregistered"
        with self.assertRaises(ValueError):
            validate_semantics(x, y)

    def test_cannot_enable_secondary_oracle_early(self):
        x, y = plans()
        x["cases"][0]["secondary_oracle_enabled"] = True
        with self.assertRaises(ValueError):
            validate_semantics(x, y)

    def test_cannot_claim_outputs_are_already_frozen(self):
        x, y = plans()
        x["cases"][0]["expected_outputs_defined"] = True
        with self.assertRaises(ValueError):
            validate_semantics(x, y)

    def test_module_and_class_test_definitions(self):
        result = collect_definitions(
            "def test_a(): pass\n"
            "class TestB:\n    def test_b(self): pass\n"
            "    async def test_c(self): pass\n")
        self.assertEqual(result["static_definitions"],
                         ["TestB.test_b", "TestB.test_c", "test_a"])
        self.assertFalse(result["definition_ids_are_runtime_test_ids"])

    def test_parametrization_not_expanded_into_invented_ids(self):
        src = "@pytest.mark.parametrize('x',[1,2])\ndef test_p(x): pass\n"
        result = collect_definitions(src)
        self.assertEqual(result["parametrized_definitions"], ["test_p"])
        self.assertEqual(result["definition_count"], 1)

    def test_nested_helper_is_not_test_definition(self):
        result = collect_definitions(
            "def test_outer():\n"
            "    def test_inner(): pass\n")
        self.assertEqual(result["static_definitions"], ["test_outer"])

    def test_source_is_only_parsed_never_executed(self):
        result = collect_definitions(
            "raise SystemExit('PRIVATE')\ndef test_real(): pass\n")
        self.assertEqual(result["static_definitions"], ["test_real"])

    def test_empty_suite_rejected(self):
        with self.assertRaises(ValueError):
            collect_definitions("def helper(): pass\n")

    def test_duplicate_top_level_names_rejected(self):
        with self.assertRaises(ValueError):
            collect_definitions(
                "def test_a(): pass\ndef test_a(): pass\n")

    def test_deterministic_static_id_hash(self):
        a = collect_definitions("def test_a(): pass\ndef test_b(): pass\n")
        b = collect_definitions("def test_b(): pass\ndef test_a(): pass\n")
        self.assertEqual(a["static_id_list_sha256"],
                         b["static_id_list_sha256"])

    def test_mocked_source_inspection_retains_blob_sha(self):
        case = {"id": "black-1", "project": "black",
                "fixed": "b"*40, "test_file": "tests/test_sample.py"}
        with patch("lab.exp009e_testbank.github_json",
                   return_value=source()):
            result = inspect_case(case, {"repo": "psf/black"})
        self.assertEqual(result["status"], "static_ast_inventory_only")
        self.assertEqual(result["file_blob_sha"], "a"*40)

    def test_source_failure_sanitized(self):
        case = {"id": "black-1", "project": "black",
                "fixed": "b"*40, "test_file": "tests/test_sample.py"}
        with patch("lab.exp009e_testbank.github_json",
                   side_effect=ValueError("private@example.com SECRET")):
            result = inspect_case(case, {"repo": "psf/black"})
        self.assertEqual(result["status"], "blocked")
        self.assertNotIn("SECRET", json.dumps(result))
        self.assertNotIn("private@", json.dumps(result))

    def test_nonregistered_project_rejected_before_network(self):
        with self.assertRaises(ValueError):
            inspect_project("unlisted")


if __name__ == "__main__":
    unittest.main()
