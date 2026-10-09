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

import nonreg_report as nr


def by_id(cases):
    return {c.nr_id: c for c in cases}


class JunitTest(unittest.TestCase):
    def test_go(self):
        outcome = nr.parse_junit(FIXTURES / "junit_go.xml")
        cases = by_id(outcome.cases)
        self.assertEqual(sorted(cases), ["NR-server-backend-12", "NR-server-backend-13", "NR-server-backend-14"])
        self.assertEqual(cases["NR-server-backend-12"].issue, "#45")
        self.assertEqual(cases["NR-server-backend-12"].status, "passed")
        self.assertEqual(cases["NR-server-backend-13"].status, "failed")
        self.assertEqual(cases["NR-server-backend-13"].issue, "essensys-hub/essensys-server-backend#51")
        self.assertEqual(cases["NR-server-backend-14"].issue, "#60")

    def test_gradle(self):
        cases = by_id(nr.parse_junit(FIXTURES / "junit_gradle.xml").cases)
        self.assertEqual(cases["NR-android-phone-apps-3"].issue, "#8")
        self.assertIn("fr.essensys.app.ShutterViewModelTest", cases["NR-android-phone-apps-3"].name)
        self.assertEqual(cases["NR-android-phone-apps-4"].status, "skipped")
        self.assertEqual(cases["NR-android-phone-apps-4"].issue, "essensys-hub/essensys-android-phone-apps#9")
        self.assertEqual(len(cases), 2)

    def test_pytest_properties(self):
        cases = by_id(nr.parse_junit(FIXTURES / "junit_pytest.xml").cases)
        self.assertEqual(cases["NR-server-backend-20"].issue, "#77")
        self.assertIsNone(cases["NR-server-backend-21"].issue)
        self.assertEqual(cases["NR-server-backend-21"].status, "failed")

    def test_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.xml"
            bad.write_text("<testsuite>", encoding="utf-8")
            self.assertTrue(nr.parse_junit(bad).errors)


class PlaywrightTest(unittest.TestCase):
    def test_parse(self):
        cases = nr.parse_playwright(FIXTURES / "playwright.json").cases
        ids = [c.nr_id for c in cases]
        self.assertEqual(ids.count("NR-server-frontend-3"), 2)
        self.assertNotIn(None, ids)
        frontend4 = next(c for c in cases if c.nr_id == "NR-server-frontend-4")
        self.assertEqual(frontend4.issue, "essensys-hub/essensys-server-frontend#30")
        self.assertTrue(frontend4.retried_pass)
        self.assertEqual(frontend4.source, "tests/e2e/scenarios.spec.ts")
        statuses = sorted(c.status for c in cases if c.nr_id == "NR-server-frontend-3")
        self.assertEqual(statuses, ["failed", "passed"])

    def test_nr_tag_without_id_is_error(self):
        data = {"suites": [{"title": "a", "specs": [{"title": "x @nr", "tags": ["@nr"],
                                                       "tests": [{"results": [{"status": "passed"}]}]}]}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pw.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            report = nr.build_report([nr.parse_playwright(path)], generated_at="t")
        self.assertEqual(report["tests"], [])
        self.assertIn("without an `NR-<repo>-<n>`", report["errors"][0])


class ReportTest(unittest.TestCase):
    def build(self, previous=None):
        outcomes = [nr.parse_input(FIXTURES / name) for name in
                    ("junit_go.xml", "junit_gradle.xml", "junit_pytest.xml", "playwright.json")]
        return nr.build_report(outcomes, previous, generated_at="2026-10-09T03:00:00Z")

    def test_aggregation_and_totals(self):
        report = self.build()
        tests = {t["id"]: t for t in report["tests"]}
        self.assertEqual(tests["NR-server-frontend-3"]["status"], "failed")
        self.assertEqual(tests["NR-server-frontend-3"]["cases"], 2)
        self.assertTrue(tests["NR-server-frontend-4"]["flaky"])
        self.assertEqual(report["totals"], {"passed": 6, "failed": 3, "skipped": 1, "flaky": 1})
        self.assertEqual(len(report["errors"]), 2)
        self.assertTrue(any("NR-server-backend-21" in e for e in report["errors"]))
        self.assertTrue(any("NR-server-frontend-5" in e for e in report["errors"]))

    def test_history_extended_and_capped(self):
        previous = {"NR-server-backend-12": ["failed", "passed"] * 5, "NR-server-backend-13": ["passed"]}
        tests = {t["id"]: t for t in self.build(previous)["tests"]}
        self.assertEqual(len(tests["NR-server-backend-12"]["history"]), 10)
        self.assertEqual(tests["NR-server-backend-12"]["history"][-1], "passed")
        self.assertTrue(tests["NR-server-backend-12"]["flaky"])
        self.assertEqual(tests["NR-server-backend-13"]["history"], ["passed", "failed"])

    def test_markdown(self):
        md = nr.emit_markdown(self.build())
        self.assertIn("| `NR-server-backend-13` | FAILED |", md)
        self.assertIn("## Errors", md)


class CliTest(unittest.TestCase):
    def test_cli_writes_outputs_and_fails_on_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            prev = Path(tmp) / "prev.json"
            prev.write_text(json.dumps({"tests": [{"id": "NR-server-backend-12", "history": ["failed"]}]}),
                            encoding="utf-8")
            out, md = Path(tmp) / "r.json", Path(tmp) / "r.md"
            buf = io.StringIO()
            with mock.patch.dict(os.environ, {}, clear=False), redirect_stdout(buf):
                os.environ.pop("GITHUB_STEP_SUMMARY", None)
                code = nr.main(["--history", str(prev), "--out", str(out), "--markdown", str(md),
                                str(FIXTURES / "junit_go.xml"), str(FIXTURES / "junit_pytest.xml")])
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(code, 1)
            self.assertEqual(report["tests"][0]["history"], ["failed", "passed"])
            self.assertTrue(md.read_text(encoding="utf-8").startswith("# Non-Regression Report"))

    def test_cli_clean_inputs_exit_zero_and_directory_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp) / "build/test-results/testDebugUnitTest"
            results.mkdir(parents=True)
            (results / "TEST-shutter.xml").write_text((FIXTURES / "junit_gradle.xml").read_text(encoding="utf-8"),
                                                      encoding="utf-8")
            out, md = Path(tmp) / "r.json", Path(tmp) / "r.md"
            with redirect_stdout(io.StringIO()):
                code = nr.main(["--out", str(out), "--markdown", str(md), str(Path(tmp) / "build")])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["totals"]["passed"], 1)

    def test_missing_input_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with redirect_stdout(io.StringIO()):
                code = nr.main(["--out", f"{tmp}/r.json", "--markdown", f"{tmp}/r.md", f"{tmp}/nope/*.xml"])
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()


class UnderscoreIdAndSourcesTest(unittest.TestCase):
    """Kotlin/Go : l'id est dans le nom (NR_android_3) et l'issue dans un commentaire `// NR:` du source."""

    def test_underscore_id_in_name_is_normalized(self) -> None:
        self.assertEqual(nr.nr_from_text("lighting_sends_salon_NR_android_5"), ("NR-android-5", None))
        self.assertEqual(
            nr.nr_from_text("TestInject_NR_server_backend_12"), ("NR-server-backend-12", None)
        )

    def test_sources_supply_missing_issue(self) -> None:
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "LightTest.kt").write_text(
                "// NR: NR-android-5 essensys-hub/essensys-android-phone-apps#4\n"
                "@Test fun lighting_sends_salon_NR_android_5() {}\n",
                encoding="utf-8",
            )
            xml = root / "TEST-light.xml"
            xml.write_text(
                '<testsuite><testcase classname="fr.essensys.LightTest" '
                'name="lighting_sends_salon_NR_android_5"/></testsuite>',
                encoding="utf-8",
            )
            out, md = root / "r.json", root / "r.md"
            code = nr.main([str(xml), "--sources", str(root / "src"), "--out", str(out), "--markdown", str(md)])
            report = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(report["tests"][0]["id"], "NR-android-5")
        self.assertEqual(report["tests"][0]["issue"], "essensys-hub/essensys-android-phone-apps#4")

