"""Offline synthetic tests for source-only EXP-009B verification."""
import base64
import io
import json
from unittest import TestCase
from unittest.mock import patch

from lab.exp009b_source_preflight import (
    content_metadata, github_json, verify_case, verify_project, REPOS,
)


def file_(path="LICENSE", text="The MIT License\nPermission is hereby granted"):
    payload = text.encode("utf-8")
    return {"type": "file", "path": path, "size": len(payload),
            "sha": "a" * 40, "encoding": "base64",
            "content": base64.b64encode(payload).decode("ascii")}


def candidate():
    return {"id": "black-1", "project": "black",
            "buggy": "a" * 40, "fixed": "b" * 40,
            "test_file": "tests/test_black.py"}


def project():
    return {"repo": "psf/black", "license_path": "LICENSE", "license": "MIT"}


def responses():
    return [
        {"sha": "b" * 40, "parents": [{"sha": "a" * 40}]},
        file_(), file_(),
        file_("tests/test_black.py", "def test_source(): assert True"),
    ]


class SourcePreflightTests(TestCase):
    def test_license_decoded_without_publishing_text(self):
        v = content_metadata(file_(), expected_path="LICENSE", license_kind="MIT")
        self.assertEqual(set(v), {"sha", "size"})
        self.assertNotIn("permission", json.dumps(v).lower())

    def test_license_wrong_family_rejected(self):
        with self.assertRaises(ValueError):
            content_metadata(file_(), expected_path="LICENSE",
                             license_kind="BSD-3-Clause")

    def test_relative_path_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            content_metadata(file_("LICENSE"), expected_path="LICENSE.md")

    def test_empty_source_rejected(self):
        q = file_()
        q["size"] = 0
        with self.assertRaises(ValueError):
            content_metadata(q, expected_path="LICENSE")

    def test_invalid_blob_sha_rejected(self):
        q = file_()
        q["sha"] = "nope"
        with self.assertRaises(ValueError):
            content_metadata(q, expected_path="LICENSE")

    def test_json_source_mock_is_not_executed(self):
        with patch("lab.exp009b_source_preflight.github_json", side_effect=responses()) as p:
            r = verify_case(candidate(), project())
        self.assertEqual(r["status"], "metadata_verified")
        self.assertEqual(len(r["files"]), 3)
        self.assertEqual(p.call_count, 4)

    def test_parent_difference_blocks_case(self):
        wrong = responses()
        wrong[0] = {"sha": "b" * 40, "parents": [{"sha": "c" * 40}]}
        with patch("lab.exp009b_source_preflight.github_json", side_effect=wrong):
            r = verify_case(candidate(), project())
        self.assertEqual(r["status"], "blocked")
        self.assertFalse(r["checks"]["parent"])

    def test_missing_license_blocks_case(self):
        sources = responses()
        sources[1] = {"message": "Not Found"}
        with patch("lab.exp009b_source_preflight.github_json", side_effect=sources):
            r = verify_case(candidate(), project())
        self.assertEqual(r["status"], "blocked")
        self.assertTrue(r["checks"]["parent"])
        self.assertFalse(r["checks"]["license_buggy"])

    def test_missing_test_blocks_case(self):
        sources = responses()
        sources[3] = {"message": "Not Found"}
        with patch("lab.exp009b_source_preflight.github_json", side_effect=sources):
            r = verify_case(candidate(), project())
        self.assertEqual(r["status"], "blocked")
        self.assertTrue(r["checks"]["license_fixed"])
        self.assertFalse(r["checks"]["fixed_test"])

    def test_failure_reason_does_not_include_secrets(self):
        with patch("lab.exp009b_source_preflight.github_json",
                   side_effect=ValueError("access-token SECRET private@example.com")):
            r = verify_case(candidate(), project())
        self.assertNotIn("SECRET", json.dumps(r))
        self.assertNotIn("private@", json.dumps(r))
        self.assertEqual(r["reason"], "source_metadata_or_network_check_failed")

    def test_github_api_repo_allowlist(self):
        with self.assertRaises(ValueError):
            github_json("attacker/untrusted", "/contents/secrets")

    def test_github_api_path_allowlist(self):
        with self.assertRaises(ValueError):
            github_json(REPOS["black"], "/actions/secrets")

    def test_authorization_only_with_explicit_token(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self, n): return b'{"ok": true}'
        with patch("lab.exp009b_source_preflight.request.urlopen", return_value=Response()) as opener:
            x = github_json("psf/black", "/commits/" + "b" * 40, token="SECRET")
        req = opener.call_args.args[0]
        self.assertEqual(req.full_url.split("/")[2], "api.github.com")
        self.assertEqual(req.headers["Authorization"], "Bearer SECRET")
        self.assertEqual(x["ok"], True)

    def test_invalid_project_rejected_before_network(self):
        with self.assertRaises(ValueError):
            verify_project("unlisted")

    def test_offline_manifest_stays_unscored(self):
        # The selected manifest contains no observed failures or results.
        from lab.exp009b_candidates import MANIFEST, validate_manifest
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(validate_manifest(m)["scores_generated"], 0)
        self.assertTrue(all(c["test_suite_execution"] == "not_executed"
                            for c in m["cases"]))


if __name__ == "__main__":
    import unittest
    unittest.main()
