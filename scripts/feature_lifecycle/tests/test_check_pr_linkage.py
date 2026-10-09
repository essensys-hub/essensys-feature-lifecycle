from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from scripts.feature_lifecycle.tests._helpers import FIXTURES

import check_pr_linkage as cpl

OK_BODY = (FIXTURES / "pr_body_ok.md").read_text(encoding="utf-8")
MISSING_BODY = (FIXTURES / "pr_body_missing.md").read_text(encoding="utf-8")


class CheckLinkageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "internal").mkdir()
        (self.root / "internal/exchange_test.go").write_text(
            "func TestRestore(t *testing.T) {\n\t// NR: NR-server-backend-13 #51\n}\n", encoding="utf-8")
        (self.root / "internal/other_test.go").write_text("// NR: NR-server-backend-14 #510\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_ok(self):
        result = cpl.check_linkage(OK_BODY)
        self.assertTrue(result.ok)
        self.assertEqual(result.feature_id, "exchange-restore-2026-10-001")

    def test_missing_feature_and_refs(self):
        result = cpl.check_linkage(MISSING_BODY)
        self.assertEqual(len(result.errors), 2)
        self.assertIn("Feature", result.errors[0])

    def test_dependabot_and_label_exempt(self):
        self.assertTrue(cpl.check_linkage(MISSING_BODY, author="dependabot[bot]").exempt)
        self.assertTrue(cpl.check_linkage(MISSING_BODY, labels=["chore/no-feature"]).ok)

    def test_bug_requires_nr_test(self):
        result = cpl.check_linkage(OK_BODY, closes_bugs=[51], changed_files=["internal/exchange_test.go"],
                                   repo_root=self.root)
        self.assertTrue(result.ok, result.errors)

    def test_bug_without_nr_test_fails_and_number_is_exact(self):
        result = cpl.check_linkage(OK_BODY, closes_bugs=[51], changed_files=["internal/other_test.go", "missing.go"],
                                   repo_root=self.root)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("#51", result.errors[0])

    def test_nr_exempt_label(self):
        result = cpl.check_linkage(OK_BODY, closes_bugs=[51], labels=["nr-exempt"], repo_root=self.root)
        self.assertTrue(result.ok)
        self.assertEqual(len(result.warnings), 1)

    def test_features_dir(self):
        features = self.root / "features"
        features.mkdir()
        self.assertFalse(cpl.check_linkage(OK_BODY, features_dir=features).ok)
        (features / "exchange-restore-2026-10-001.json").write_text("{}", encoding="utf-8")
        self.assertTrue(cpl.check_linkage(OK_BODY, features_dir=features).ok)


class CliTest(unittest.TestCase):
    def run_cli(self, argv, env=None):
        buf = io.StringIO()
        with mock.patch.dict(os.environ, env or {}, clear=False), redirect_stdout(buf):
            os.environ.pop("GITHUB_STEP_SUMMARY", None)
            code = cpl.main(argv)
        return code, buf.getvalue()

    def test_warn_mode_exits_zero(self):
        code, out = self.run_cli(["--pr-body-file", str(FIXTURES / "pr_body_missing.md"), "--mode", "warn"])
        self.assertEqual(code, 0)
        self.assertIn("Feature: <feature-id>", out)

    def test_block_mode_exits_one(self):
        code, _ = self.run_cli(["--pr-body-file", str(FIXTURES / "pr_body_missing.md"), "--mode", "block"])
        self.assertEqual(code, 1)

    def test_mode_from_env(self):
        with mock.patch.dict(os.environ, {"FEATURE_GATE_MODE": "block"}):
            code, _ = self.run_cli(["--pr-body-file", str(FIXTURES / "pr_body_missing.md")])
        self.assertEqual(code, 1)

    def test_json_and_step_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = Path(tmp) / "summary.md"
            changed = Path(tmp) / "changed.txt"
            changed.write_text("x.go\n", encoding="utf-8")
            buf = io.StringIO()
            with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(summary)}), redirect_stdout(buf):
                code = cpl.main(["--pr-body-file", str(FIXTURES / "pr_body_ok.md"), "--json", "--mode", "block",
                                 "--closes-bug-numbers", "51", "--changed-files-file", str(changed),
                                 "--repo-root", tmp])
            payload = json.loads(buf.getvalue())
            self.assertEqual(code, 1)
            self.assertFalse(payload["ok"])
            self.assertIn("PR Linkage Check", summary.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
