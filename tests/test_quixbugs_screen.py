import json
from pathlib import Path
import tempfile
import unittest
from lab.quixbugs_screen import PROGRAMS, canonical, read_fixtures, invoke

class QuixbugsScreenTests(unittest.TestCase):
    def test_curated_program_count(self):
        self.assertEqual(len(PROGRAMS), 20)
        self.assertEqual(len(set(PROGRAMS)), len(PROGRAMS))

    def test_linewise_fixtures(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'fixture.json'
            path.write_text('[[1], 2]\n[[3, 4], 7]\n')
            self.assertEqual(read_fixtures(path), [([1], 2), ([3,4],7)])

    def test_bad_fixtures_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'fixture.json'
            path.write_text('[1, 2]\n')
            with self.assertRaises(ValueError): read_fixtures(path)

    def test_canonicalization(self):
        self.assertEqual(canonical((1,(2,3))), [1,[2,3]])
        self.assertEqual(canonical({3,1}), [1,3])

    def test_invoke_copies_arguments(self):
        original = [1]
        def mutate(x):
            x.append(2)
            return x
        self.assertEqual(invoke(mutate, [original])['value'], [1,2])
        self.assertEqual(original, [1])

    def test_exception_is_not_ignored(self):
        def fail(x): raise ValueError('X')
        self.assertEqual(invoke(fail, [1])['status'], 'exception')

if __name__ == '__main__':unittest.main()
