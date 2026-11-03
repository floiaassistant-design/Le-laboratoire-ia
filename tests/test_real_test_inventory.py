"""Offline, no-execution tests for static test-inventory infrastructure."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lab.real_test_inventory import (
    inventory_source, scan_directory, write_report, _bucket,
)


class RealTestInventoryTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.root = Path(self.dir.name)
        self.tests = self.root / "tests"
        self.tests.mkdir()

    def create(self, name, source):
        path = self.tests / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return path

    def test_plain_and_async_functions(self):
        code = """\
def test_one():
    assert 1 == 1
async def test_two():
    assert True
def helper():
    assert 0
def outer():
    def test_nested():
        assert True
"""
        rows = inventory_source(code, "tests/test_sample.py")
        self.assertEqual([r["function"] for r in rows], ["test_one", "test_two"])
        self.assertEqual(rows[0]["structure_counts"]["asserts"], 1)
        self.assertTrue(rows[1]["is_async"])

    def test_unittest_and_pytest_classes(self):
        code = """\
import unittest
class Other(unittest.TestCase):
    def test_unittest(self):
        self.assertTrue(True)
class TestFoo:
    def test_pytest(self):
        assert True
class NotTest:
    def test_excluded(self):
        assert True
"""
        rows = inventory_source(code, "tests/test_class.py")
        self.assertEqual([r["function"] for r in rows],
                         ["test_unittest", "test_pytest"])
        self.assertEqual([r["kind"] for r in rows],
                         ["unittest_method", "pytest_method"])

    def test_decorator_marked_but_not_expanded(self):
        code = """\
@pytest.mark.parametrize("x", [1, 2, 3])
def test_many(x):
    assert x
"""
        rows = inventory_source(code, "tests/test_params.py")
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["parametrized_definition"])
        self.assertEqual(rows[0]["nodeid"], "tests/test_params.py::test_many")

    def test_ast_not_runtime_exec(self):
        self.create("test_noexec.py", "raise RuntimeError('MUST NEVER RUN')\n"
                    "def test_safe():\n    assert True\n")
        result = scan_directory(self.root)
        self.assertEqual(result["candidate_definitions"], 1)
        self.assertFalse(result["code_executed"])
        self.assertEqual(result["bugs_scored"], 0)

    def test_ignored_non_test_files(self):
        self.create("helper.py", "def test_hidden(): pass")
        self.create("test_yes.py", "def test_yes(): pass")
        self.create("outside.txt", "def test_no(): pass")
        result = scan_directory(self.root)
        self.assertEqual(result["file_candidates"], 1)
        self.assertEqual(result["candidate_definitions"], 1)

    def test_recursive_deterministic_inventory(self):
        self.create("sub/test_z.py", "def test_z(): pass")
        self.create("test_a.py", "def test_a(): pass")
        one, two = scan_directory(self.root), scan_directory(self.root)
        self.assertEqual(one, two)
        self.assertEqual([x["function"] for x in one["test_candidates"]],
                         ["test_a", "test_z"])

    def test_duplicate_methods_reported(self):
        self.create("test_dup.py", "def test_same(): pass\n"
                    "def test_same(): pass\n")
        data = scan_directory(self.root)
        self.assertEqual(len(data["test_candidates"]), 2)
        self.assertEqual(data["errors"][0]["reason"], "duplicate_definition")

    def test_invalid_syntax_reported(self):
        self.create("test_bad.py", "def test_broken(:")
        result = scan_directory(self.root)
        self.assertEqual(result["errors"][0]["reason"], "syntax_error")
        self.assertEqual(result["files_parsed"], 0)

    def test_reject_escape_scan_path(self):
        with self.assertRaises(ValueError):
            scan_directory(self.root, "..")

    def test_skip_file_symlink(self):
        outside = self.root / "test_elsewhere.py"
        outside.write_text("def test_external(): pass", encoding="utf-8")
        try:
            (self.tests / "test_link.py").symlink_to(outside)
        except OSError:
            self.skipTest("Symlink unsupported")
        data = scan_directory(self.root)
        self.assertEqual(data["candidate_definitions"], 0)

    def test_skip_directory_symlink(self):
        outside = self.root / "other"
        outside.mkdir()
        (outside / "test_external.py").write_text(
            "def test_external(): pass", encoding="utf-8")
        try:
            (self.tests / "link").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink unsupported")
        data = scan_directory(self.root)
        self.assertEqual(data["candidate_definitions"], 0)

    def test_large_file_not_loaded(self):
        self.create("test_huge.py", " " * 512001)
        data = scan_directory(self.root)
        self.assertEqual(data["errors"][0]["reason"], "too_large")

    def test_report_round_trip(self):
        self.create("test_x.py", "def test_x(): pass")
        report = scan_directory(self.root)
        path = write_report(report, self.root, "results/report.json")
        parsed = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(parsed, report)
        self.assertEqual(parsed["bugs_scored"], 0)

    def test_output_cannot_escape_root(self):
        with self.assertRaises(ValueError):
            write_report({}, self.root, "../outside.json")

    def test_features_are_shape_only(self):
        code = "def test_shape():\n    for x in [1,2]:\n        if x:\n            assert True\n"
        entry = inventory_source(code, "tests/test_x.py")[0]
        self.assertEqual(entry["structure_counts"]["loops"], 1)
        self.assertEqual(entry["structure_counts"]["branches"], 1)
        self.assertFalse(any("pass" in x or "fail" in x for x in entry["static_features"]))

    def test_bucket_values(self):
        self.assertEqual([_bucket(i) for i in [0,1,2,3,4,7,8]],
                         ["0","1","2-3","2-3","4-7","4-7","8+"])


if __name__ == "__main__":
    unittest.main()
