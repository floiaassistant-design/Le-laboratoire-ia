import unittest
from pathlib import Path
from lab.realbug_isolation import worktree_path, isolated_python_env


class SourceIsolationTests(unittest.TestCase):
    def test_revisions_have_separate_worktrees(self):
        root = Path("/tmp/reproduction-test")
        old, new = worktree_path(root, "buggy"), worktree_path(root, "fixed")
        self.assertNotEqual(old, new)
        self.assertEqual(old.parent, new.parent)

    def test_only_explicit_labels(self):
        for label in ("main", "a/../../b", "", "old"):
            with self.assertRaises(ValueError):
                worktree_path(Path("/tmp/test"), label)

    def test_bytecode_cache_disabled(self):
        env = isolated_python_env(Path("/tmp/check"), {})
        self.assertEqual(env["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertEqual(env["PYTHONNOUSERSITE"], "1")

    def test_replaces_stale_pythonpath_without_mutating_base(self):
        original = {"PYTHONPATH": "/previous-checkout", "OTHER": "keep"}
        env = isolated_python_env(Path("/tmp/current-checkout"), original)
        self.assertEqual(original["PYTHONPATH"], "/previous-checkout")
        self.assertEqual(env["PYTHONPATH"], "/tmp/current-checkout")
        self.assertEqual(env["OTHER"], "keep")

    def test_each_revision_gets_own_python_import_path(self):
        root = Path("/tmp/independent-checks")
        a = isolated_python_env(worktree_path(root, "buggy"), {})
        b = isolated_python_env(worktree_path(root, "fixed"), {})
        self.assertNotEqual(a["PYTHONPATH"], b["PYTHONPATH"])

if __name__=="__main__":
    unittest.main()
