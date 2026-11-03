"""EXP-007B: no third-party imports; synthetic identity comparisons."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lab.real_test_collector import (
    compare_identifiers, run_comparison, collect_unittest_identifiers,
    _flatten_tests, _canonical_test_id
)


class CollectionIdentityTests(unittest.TestCase):
    def test_equal_but_different_identities_is_failure(self):
        compared = compare_identifiers(["tests/test_a.py::A::test_a"],
                                       ["tests/test_b.py::B::test_b"])
        self.assertEqual(compared["static_count"], compared["runtime_count"])
        self.assertFalse(compared["exact_identity_multiset_match"])
        self.assertEqual(compared["static_only_count"], 1)
        self.assertEqual(compared["runtime_only_count"], 1)

    def test_exact_identity_match(self):
        x = ["tests/test_a.py::A::test_a", "tests/test_a.py::A::test_b"]
        compared = compare_identifiers(x, list(reversed(x)))
        self.assertTrue(compared["exact_identity_multiset_match"])
        self.assertEqual(compared["static_identity_sha256"],
                         compared["runtime_identity_sha256"])

    def test_duplicate_not_hidden_by_sets(self):
        x = ["tests/test_a.py::A::test_a"] * 2
        y = ["tests/test_a.py::A::test_a"]
        compared = compare_identifiers(x, y)
        self.assertFalse(compared["exact_identity_multiset_match"])
        self.assertEqual(compared["static_duplicates"], x[:1])

    def test_empty_lists_match_but_cannot_be_a_valid_run(self):
        self.assertTrue(compare_identifiers([], [])["exact_identity_multiset_match"])

    def test_require_opt_in(self):
        with self.assertRaises(PermissionError):
            collect_unittest_identifiers(Path.cwd(), allow_imports=False)
        with self.assertRaises(PermissionError):
            run_comparison(Path.cwd(), allow_imports=False)

    def test_refuse_outside_root_discovery(self):
        with self.assertRaises(ValueError):
            collect_unittest_identifiers(Path.cwd(), scan_dir="../",
                                         allow_imports=True)

    def test_flatten_suite_does_not_call_test(self):
        class FailingWhenRun(unittest.TestCase):
            def test_bad(self):
                raise AssertionError("MUST NOT EXECUTE")
        suite = unittest.TestSuite([unittest.TestSuite(
            [FailingWhenRun("test_bad")])])
        output = list(_flatten_tests(suite))
        self.assertEqual(len(output), 1)
        self.assertIsInstance(output[0], FailingWhenRun)

    def test_flatten_rejects_unknown_object(self):
        suite = unittest.TestSuite()
        # _tests is an implementation detail; synthetic error-path check.
        suite._tests = [object()]
        with self.assertRaises(ValueError):
            list(_flatten_tests(suite))

    def test_canonical_id_existing_own_test_case(self):
        test = CollectionIdentityTests("test_exact_identity_match")
        result = _canonical_test_id(test, Path.cwd())
        self.assertEqual(result, "tests/test_real_test_collector.py::"
                                 "CollectionIdentityTests::test_exact_identity_match")

    def test_canonical_id_rejects_non_case(self):
        with self.assertRaises(ValueError):
            _canonical_test_id(object(), Path.cwd())

    def test_python_candidate_only_is_reported_as_static_only(self):
        result = compare_identifiers(
            ["tests/test_x.py::test_simple"], [])
        self.assertEqual(result["static_only"], ["tests/test_x.py::test_simple"])

    def test_inherited_method_is_reported_as_runtime_only(self):
        expected = "tests/test_x.py::Child::test_inherited"
        result = compare_identifiers([], [expected])
        self.assertEqual(result["runtime_only"], [expected])

    def test_deterministic_digest(self):
        x = ["tests/test_y.py::B::test_b","tests/test_a.py::A::test_a"]
        self.assertEqual(compare_identifiers(x,x),
                         compare_identifiers(x[::-1],x[::-1]))

    def test_invalid_test_case_method(self):
        class Example(unittest.TestCase):
            def test_ok(self):
                pass
        test = Example("test_ok")
        # The in-memory class has a nested qualname; fail closed.
        with self.assertRaises(ValueError):
            _canonical_test_id(test, Path.cwd())


if __name__ == "__main__":
    unittest.main()
