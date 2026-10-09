from __future__ import annotations

import unittest

from scripts.feature_lifecycle.tests._helpers import FIXTURES  # noqa: F401  (chemin des scripts)

import xcresult_to_junit as xj


SAMPLE = {"testNodes": [{"nodeType": "Test Plan", "name": "app", "children": [
    {"nodeType": "Unit test bundle", "name": "appTests", "children": [
        {"nodeType": "Test Suite", "name": "IndexTableTests", "children": [
            {"nodeType": "Test Case", "name": "lighting_sends_portal_index_and_mask_NR_ios_5()", "result": "Passed"},
            {"nodeType": "Test Case", "name": "broken()", "result": "Failed",
             "children": [{"nodeType": "Failure Message", "name": "Expectation failed"}]},
            {"nodeType": "Test Case", "name": "later()", "result": "Skipped"},
        ]},
    ]},
]}]}


class XcresultToJunitTest(unittest.TestCase):
    def test_cases_statuses_and_names(self) -> None:
        root = xj.to_junit(SAMPLE)
        suite = root.find("testsuite")
        self.assertEqual(suite.get("name"), "IndexTableTests")
        self.assertEqual((suite.get("tests"), suite.get("failures"), suite.get("skipped")), ("3", "1", "1"))
        names = [c.get("name") for c in suite.findall("testcase")]
        self.assertEqual(names[0], "lighting_sends_portal_index_and_mask_NR_ios_5")
        self.assertEqual(suite.findall("testcase")[1].find("failure").get("message"), "Expectation failed")

    def test_runner_error_is_reported(self) -> None:
        class Done:
            returncode, stdout, stderr = 1, "", "boom"
        with self.assertRaises(RuntimeError):
            xj.load_tests("x.xcresult", runner=lambda *a, **k: Done())


if __name__ == "__main__":
    unittest.main()
