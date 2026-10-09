from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.feature_lifecycle.tests._helpers import FIXTURES, FakeRunner, item_node

import project_sync as ps


class NextStatusTest(unittest.TestCase):
    def test_forward_only(self):
        self.assertEqual(ps.next_status("Spec", "En cours"), "En cours")
        self.assertIsNone(ps.next_status("Test", "En cours"))
        self.assertIsNone(ps.next_status("Test", "Test"))

    def test_unknown_or_empty_status_is_before_idee(self):
        for legacy in (None, "", "Backlog", "To triage"):
            self.assertEqual(ps.next_status(legacy, "Idée"), "Idée")
            self.assertEqual(ps.next_status(legacy, "Spec"), "Spec")

    def test_unknown_target_raises(self):
        with self.assertRaises(ValueError):
            ps.next_status("Spec", "Done")

    def test_event_targets_cover_all_statuses_but_idee(self):
        self.assertEqual(sorted(ps.EVENT_TARGETS.values(), key=ps.STATUSES.index), ps.STATUSES[1:])


class ParsePrBodyTest(unittest.TestCase):
    def test_full_body_ignores_html_comments(self):
        links = ps.parse_pr_body((FIXTURES / "pr_body_ok.md").read_text(encoding="utf-8"))
        self.assertEqual(links.feature_id, "exchange-restore-2026-10-001")
        self.assertEqual(links.closes, ["#51", "essensys-hub/essensys-user-portal-backend#7"])
        self.assertEqual(links.refs, ["#42"])
        self.assertNotIn("#999", links.closes)

    def test_missing_everything(self):
        links = ps.parse_pr_body((FIXTURES / "pr_body_missing.md").read_text(encoding="utf-8"))
        self.assertIsNone(links.feature_id)
        self.assertEqual(links.closes, [])
        self.assertEqual(links.refs, [])

    def test_case_insensitive_and_cross_repo_refs(self):
        links = ps.parse_pr_body((FIXTURES / "pr_body_refs_only.md").read_text(encoding="utf-8"))
        self.assertEqual(links.feature_id, "ui-scenarios-2026-10-002")
        self.assertEqual(links.refs, ["essensys-hub/essensys-feature-lifecycle#42"])

    def test_invalid_feature_id_rejected(self):
        self.assertIsNone(ps.parse_pr_body("Feature: Bad_ID\nCloses #1").feature_id)
        self.assertIsNone(ps.parse_pr_body(None).feature_id)

    def test_resolves_variants(self):
        links = ps.parse_pr_body("Feature: a-1\nResolves #3\nclosed #4\nFixed #5")
        self.assertEqual(links.closes, ["#3", "#4", "#5"])


class GhClientTest(unittest.TestCase):
    def test_project_fields_and_options(self):
        client = ps.GhClient(FakeRunner())
        project = client.project()
        self.assertEqual(project["id"], "PVT_1")
        self.assertEqual(project["fields"]["Status"]["options"]["Test"], "O_4")

    def test_find_item_prefers_feature_type(self):
        runner = FakeRunner(items=[
            item_node("PVTI_task", "x-2026-10-001", "En cours", issue_type="Task"),
            item_node("PVTI_feat", "x-2026-10-001", "Spec", issue_type="Feature"),
            item_node("PVTI_other", "y-2026-10-001", "Spec"),
        ])
        item = ps.GhClient(runner).find_item_by_feature_id("x-2026-10-001")
        self.assertEqual(item["id"], "PVTI_feat")
        self.assertEqual(item["fields"]["Status"], "Spec")
        self.assertIsNone(ps.GhClient(runner).find_item_by_feature_id("zzz"))

    def test_item_for_issue_filters_project(self):
        item = ps.GhClient(FakeRunner()).item_for_issue("essensys-server-backend", 12)
        self.assertEqual(item["id"], "PVTI_issue")
        self.assertEqual(item["fields"]["Status"], "Test")

    def test_dry_run_prints_and_does_not_mutate(self):
        runner, printed = FakeRunner(), []
        client = ps.GhClient(runner, dry_run=True, out=printed.append)
        self.assertIsNone(client.set_single_select("PVTI_1", "Status", "Test"))
        client.set_text("PVTI_1", "Feature ID", "x-1")
        client.comment("essensys-server-backend", 3, "hello")
        self.assertEqual(runner.mutations(), [])
        self.assertEqual(len(printed), 3)
        self.assertIn("[dry-run]", printed[0])

    def test_apply_sends_mutation(self):
        runner = FakeRunner()
        client = ps.GhClient(runner, dry_run=False)
        client.set_single_select("PVTI_1", "Status", "Test")
        (query, variables), = runner.mutations()
        self.assertIn("updateProjectV2ItemFieldValue", query)
        self.assertEqual(variables, {"project": "PVT_1", "item": "PVTI_1", "field": "F_status", "option": "O_4"})

    def test_unknown_option_raises(self):
        with self.assertRaises(ps.GhError):
            ps.GhClient(FakeRunner()).set_single_select("PVTI_1", "Status", "Done")

    def test_search_issues_normalized(self):
        runner = FakeRunner(search=[{"number": 5, "title": "t", "body": "b", "url": "u", "state": "OPEN",
                                     "repository": {"name": "essensys-server-backend"},
                                     "labels": {"nodes": [{"name": "regression"}]}}])
        bugs = ps.GhClient(runner).search_issues("label:regression")
        self.assertEqual(bugs[0]["repo"], "essensys-server-backend")
        self.assertEqual(bugs[0]["labels"], ["regression"])


class AdvanceTest(unittest.TestCase):
    def test_advances_forward(self):
        runner = FakeRunner(items=[item_node("PVTI_f", "x-2026-10-001", "En cours")])
        result = ps.advance(ps.GhClient(runner, dry_run=False), "x-2026-10-001", "all-prs-merged")
        self.assertEqual(result.applied_status, "Test")
        self.assertEqual(runner.mutations()[0][1]["option"], "O_4")

    def test_never_regresses(self):
        runner = FakeRunner(items=[item_node("PVTI_f", "x-2026-10-001", "Gate sécu")])
        result = ps.advance(ps.GhClient(runner, dry_run=False), "x-2026-10-001", "pr-opened")
        self.assertIsNone(result.applied_status)
        self.assertEqual(runner.mutations(), [])

    def test_legacy_status_advances(self):
        runner = FakeRunner(items=[item_node("PVTI_f", "x-2026-10-001", "Backlog")])
        result = ps.advance(ps.GhClient(runner, dry_run=True, out=lambda _: None), "x-2026-10-001", "spec-created")
        self.assertEqual(result.applied_status, "Spec")

    def test_missing_item(self):
        result = ps.advance(ps.GhClient(FakeRunner()), "nope-1", "ready")
        self.assertIsNone(result.item_id)

    def test_unknown_event(self):
        with self.assertRaises(ValueError):
            ps.advance(ps.GhClient(FakeRunner()), "x", "merged")


def nr_test(nr_id, status, history, issue="#12", name="restaure la table"):
    return {"id": nr_id, "name": name, "source": "junit_go.xml", "status": status, "issue": issue, "history": history}


def open_bug(nr_id, number=40, labels=("regression",), repo="essensys-server-backend"):
    return {"number": number, "repo": repo, "state": "OPEN", "labels": list(labels),
            "body": f"<!-- nr:{nr_id} -->\nDescription"}


class RegressionActionsTest(unittest.TestCase):
    def test_new_failure_opens_bug(self):
        report = {"generated_at": "2026-10-09T02:00:00Z", "report_url": "https://reports/1",
                  "tests": [nr_test("NR-server-backend-12", "failed", ["passed", "failed"])]}
        (action,) = ps.regression_actions(report, [])
        self.assertEqual(action.kind, "open_bug")
        self.assertEqual(action.repo, "essensys-server-backend")
        self.assertEqual(action.title, "[NR] NR-server-backend-12 : restaure la table")
        self.assertEqual(action.labels, ["regression"])
        self.assertIn("<!-- nr:NR-server-backend-12 -->", action.body)
        self.assertIn("https://reports/1", action.body)
        self.assertIn("#12", action.body)

    def test_cross_repo_issue_sets_repo(self):
        report = {"tests": [nr_test("NR-server-backend-13", "failed", ["failed"],
                                    issue="essensys-hub/essensys-user-portal-backend#4")]}
        (action,) = ps.regression_actions(report, [])
        self.assertEqual(action.repo, "essensys-user-portal-backend")

    def test_existing_bug_gets_comment_not_duplicate(self):
        report = {"tests": [nr_test("NR-server-backend-12", "failed", ["failed", "failed"])]}
        actions = ps.regression_actions(report, [open_bug("NR-server-backend-12")])
        self.assertEqual([a.kind for a in actions], ["comment"])
        self.assertEqual(actions[0].number, 40)

    def test_marker_must_match_exact_id(self):
        report = {"tests": [nr_test("NR-server-backend-1", "failed", ["failed"])]}
        actions = ps.regression_actions(report, [open_bug("NR-server-backend-12")])
        self.assertEqual(actions[0].kind, "open_bug")

    def test_flaky_new_bug(self):
        report = {"tests": [nr_test("NR-x-1", "failed", ["failed", "passed", "failed"])]}
        (action,) = ps.regression_actions(report, [])
        self.assertEqual(action.labels, ["regression", "flaky"])

    def test_flaky_existing_bug_gets_label_once(self):
        report = {"tests": [nr_test("NR-x-1", "failed", ["passed", "failed", "passed", "failed"])]}
        kinds = [a.kind for a in ps.regression_actions(report, [open_bug("NR-x-1")])]
        self.assertEqual(kinds, ["comment", "add_label"])
        kinds = [a.kind for a in ps.regression_actions(report, [open_bug("NR-x-1", labels=("regression", "flaky"))])]
        self.assertEqual(kinds, ["comment"])

    def test_three_greens_propose_close(self):
        report = {"tests": [nr_test("NR-x-1", "passed", ["failed", "passed", "passed", "passed"])]}
        (action,) = ps.regression_actions(report, [open_bug("NR-x-1")])
        self.assertEqual(action.kind, "propose_close")
        self.assertIn("pas de fermeture automatique", action.body)

    def test_two_greens_do_nothing_and_no_bug_do_nothing(self):
        report = {"tests": [nr_test("NR-x-1", "passed", ["failed", "passed", "passed"])]}
        self.assertEqual(ps.regression_actions(report, [open_bug("NR-x-1")]), [])
        report = {"tests": [nr_test("NR-x-1", "passed", ["passed", "passed", "passed"])]}
        self.assertEqual(ps.regression_actions(report, []), [])

    def test_closed_bug_ignored(self):
        bug = open_bug("NR-x-1")
        bug["state"] = "CLOSED"
        report = {"tests": [nr_test("NR-x-1", "failed", ["failed"])]}
        self.assertEqual(ps.regression_actions(report, [bug])[0].kind, "open_bug")

    def test_alternations(self):
        self.assertEqual(ps.count_alternations(["passed", "skipped", "failed", "passed"]), 2)
        self.assertFalse(ps.is_flaky(["passed", "failed", "failed"]))


class ApplyActionsTest(unittest.TestCase):
    def test_open_bug_apply_creates_issue_adds_to_project_and_sets_idee(self):
        runner = FakeRunner()
        client = ps.GhClient(runner, dry_run=False)
        report = {"tests": [nr_test("NR-server-backend-12", "failed", ["failed"])]}
        ps.apply_actions(client, ps.regression_actions(report, []))
        mutations = [q for q, _ in runner.mutations()]
        self.assertTrue(any("createIssue" in q for q in mutations))
        self.assertTrue(any("addProjectV2ItemById" in q for q in mutations))
        create_vars = next(v for q, v in runner.mutations() if "createIssue" in q)
        self.assertEqual(create_vars["labels"], ["L_reg"])
        self.assertEqual(create_vars["type"], "T_bug")
        status_vars = next(v for q, v in runner.mutations() if "updateProjectV2ItemFieldValue" in q)
        self.assertEqual(status_vars["option"], "O_0")

    def test_dry_run_apply_sends_nothing(self):
        runner, printed = FakeRunner(), []
        client = ps.GhClient(runner, dry_run=True, out=printed.append)
        report = {"tests": [nr_test("NR-server-backend-12", "failed", ["failed"])]}
        log = ps.apply_actions(client, ps.regression_actions(report, [open_bug("NR-server-backend-12")]))
        self.assertEqual(runner.mutations(), [])
        self.assertEqual(len(log), 1)
        self.assertTrue(printed)


class CliTest(unittest.TestCase):
    def run_cli(self, argv, runner):
        client = ps.GhClient(runner, dry_run=True, out=lambda _: None)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = ps.main(argv, client=client)
        return code, buf.getvalue()

    def test_status(self):
        runner = FakeRunner(items=[item_node("PVTI_f", "x-2026-10-001", "Spec")])
        code, out = self.run_cli(["status", "x-2026-10-001"], runner)
        self.assertEqual(code, 0)
        self.assertIn("Status: `Spec`", out)

    def test_pr_event_dry_run_json(self):
        runner = FakeRunner(items=[item_node("PVTI_f", "exchange-restore-2026-10-001", "Prêt")])
        code, out = self.run_cli(["--json", "pr-event", "--pr-body-file", str(FIXTURES / "pr_body_ok.md"),
                                  "--event", "pr-opened"], runner)
        payload = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(payload["mode"], "dry-run")
        self.assertEqual(payload["applied_status"], "En cours")
        self.assertEqual(runner.mutations(), [])

    def test_regression_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "r.json"
            report.write_text(json.dumps({"tests": [nr_test("NR-x-1", "failed", ["failed"])]}), encoding="utf-8")
            code, out = self.run_cli(["regression", "--report", str(report), "--report-url", "https://r"], FakeRunner())
        self.assertEqual(code, 0)
        self.assertIn("open_bug essensys-x", out)


if __name__ == "__main__":
    unittest.main()
