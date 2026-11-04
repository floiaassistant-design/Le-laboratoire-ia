"""Offline tests for EXP-009C static dependency extraction; no upstream imports."""
import base64
import json
from unittest import TestCase
from unittest.mock import patch

from lab.exp009c_dependencies import (
    DESCRIPTORS, dependency_summary, inspect_case,
    inspect_project, static_profile, static_setup_summary, unpack_source,
)


def fixture_(path, text):
    b = text.encode("utf-8")
    return {"type": "file", "path": path, "size": len(b),
            "sha": "a" * 40, "encoding": "base64",
            "content": base64.b64encode(b).decode("ascii")}


class DependencyMetadataTests(TestCase):
    def test_only_four_frozen_projects(self):
        self.assertEqual(set(DESCRIPTORS), {"black", "fastapi", "httpie", "thefuck"})

    def test_exact_and_unbounded_constraints(self):
        r = dependency_summary(["pydantic>=1,<2", "starlette==0.13.2", "click", ""])
        self.assertEqual(r["declared"], 3)
        self.assertEqual(r["exact_equality_constraints"], 1)
        self.assertEqual(r["non_exact_or_unbounded_constraints"], 2)

    def test_comments_not_counted(self):
        self.assertEqual(dependency_summary(["# private note", "pytest"])["declared"], 1)

    def test_reject_non_string(self):
        with self.assertRaises(ValueError):
            dependency_summary(["safe", 42])

    def test_ast_setup_does_not_execute_code(self):
        src = "raise RuntimeError('never execute')\ninstall_requires=['requests>=2.3']\nsetup(install_requires=install_requires)\n"
        r = static_setup_summary(src)
        self.assertEqual(r["runtime_literal"]["declared"], 1)
        self.assertFalse(r["source_was_executed"])

    def test_ast_setup_dynamic_append_is_flagged(self):
        src = "install_requires=['requests>=2.3']\ninstall_requires.append('colorama')\nsetup(install_requires=install_requires)"
        self.assertTrue(static_setup_summary(src)["dynamic_requirements_present"])

    def test_ast_setup_direct_literal_list(self):
        src = "setup(install_requires=['click==7.1.1'],tests_require=['pytest'])"
        a = static_setup_summary(src)
        self.assertEqual(a["runtime_literal"]["exact_equality_constraints"], 1)
        self.assertEqual(a["test_literal"]["non_exact_or_unbounded_constraints"], 1)

    def test_lockfile_entries_not_assumed_installable(self):
        src = json.dumps({"default": {"click": {"version": "==7.0"},
                                      "local": {"path": ".", "editable": True}},
                          "develop": {"pytest": {"version": ">=5"}}})
        r = static_profile("Pipfile.lock", src)
        self.assertEqual(r["exact_locked_entries"], 1)
        self.assertEqual(r["local_or_editable_entries"], 1)
        self.assertEqual(r["unbounded_or_unclassified_entries"], 1)
        self.assertFalse(r["installability_verified"])

    def test_flit_requires_are_not_all_exact(self):
        text = ("[tool.flit.metadata]\n"
                "requires=['starlette ==0.13.2','pydantic >=0.32,<2']\n"
                "requires-python='>=3.6'\n"
                "[tool.flit.metadata.requires-extra]\n"
                "test=['pytest','requests']\n")
        r = static_profile("pyproject.toml", text)
        self.assertEqual(r["core"]["exact_equality_constraints"], 1)
        self.assertEqual(r["optional"]["non_exact_or_unbounded_constraints"], 2)

    def test_requirements_unpinned_detected(self):
        r = static_profile("requirements-dev.txt", "pytest\npytest-httpbin>=0.0.6\n")
        self.assertEqual(r["declarations"]["exact_equality_constraints"], 0)

    def test_external_includes_not_executed(self):
        r = static_profile("requirements.txt", "-r local.txt\npytest\n")
        self.assertTrue(r["has_external_or_dynamic_includes"])
        self.assertFalse(r["installability_verified"])

    def test_unknown_descriptor_rejected(self):
        with self.assertRaises(ValueError):
            static_profile("setup.cfg", "anything")

    def test_content_unpacked_only_metadata_returned(self):
        meta, body = unpack_source(fixture_("setup.py", "print('safe')"), "setup.py")
        self.assertEqual(meta["size"], len("print('safe')"))
        self.assertEqual(body, "print('safe')")

    def test_missing_source_blocked_with_no_raw_error(self):
        data = {"id": "black-1", "project": "black", "fixed": "b"*40}
        meta = {"repo": "psf/black"}
        with patch("lab.exp009c_dependencies.github_json",
                   side_effect=ValueError("SECRET@example.com")):
            r = inspect_case(data, meta)
        self.assertEqual(r["status"], "blocked")
        self.assertNotIn("SECRET", json.dumps(r))

    def test_inspect_project_requires_allowlisted_project(self):
        with self.assertRaises(ValueError):
            inspect_project("strange")


if __name__ == "__main__":
    import unittest
    unittest.main()
