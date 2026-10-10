from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.feature_lifecycle.tests._helpers import FakeRunner, item_node  # noqa: F401  (chemin des scripts)

import list_workable
import setup_triage_repo
import project_sync as ps
import triage
import triage_gate
import triage_guard


def issue(login="alice", utype="User", labels=(), state="open", number=7):
    return {"number": number, "state": state, "user": {"login": login, "type": utype},
            "labels": [{"name": n} for n in labels]}


class FakeGh:
    """Répond aux appels `gh api` de triage.check / author_role."""

    def __init__(self, issue_data, roles=None, fail=False):
        self.issue_data, self.roles, self.fail, self.calls = issue_data, roles or {}, fail, []

    def __call__(self, args):
        self.calls.append(args)
        if self.fail:
            raise triage.ReadError("HTTP 502")
        path = args[0]
        if "/collaborators/" in path:
            login = path.split("/collaborators/")[1].split("/")[0]
            if login not in self.roles:
                raise triage.ReadError("HTTP 404: Not Found")
            return {"role_name": self.roles[login], "permission": "write"}
        return self.issue_data


class MaintainerTest(unittest.TestCase):
    # NR: NR-lifecycle-2 essensys-hub/essensys-feature-lifecycle#18
    def test_bot_is_never_maintainer_NR_lifecycle_2(self):
        self.assertFalse(triage.is_maintainer("essensys-support-bot[bot]", "Bot", "admin"))
        self.assertFalse(triage.is_maintainer("renovate", "Bot", "maintain"))
        self.assertTrue(triage.is_maintainer("rhinosys", "User", "maintain"))
        self.assertTrue(triage.is_maintainer("rhinosys", "User", "admin"))
        for role in ("write", "triage", "read", "none", None):
            self.assertFalse(triage.is_maintainer("bob", "User", role))


class EvaluateTest(unittest.TestCase):
    # NR: NR-lifecycle-1 essensys-hub/essensys-feature-lifecycle#18
    def test_unvalidated_report_is_not_workable_NR_lifecycle_1(self):
        v = triage.evaluate("open", ["a-valider", "incident", "via-portal"], False)
        self.assertFalse(v.workable)
        self.assertIn("a-valider", v.reason)
        self.assertIn("valide", v.action)

    def test_blocking_label_wins_over_valide(self):
        self.assertFalse(triage.evaluate("open", ["valide", "besoin-info"], True).workable)
        self.assertFalse(triage.evaluate("open", ["valide", "a-valider"], True).workable)

    def test_validated_or_maintainer_ticket_is_workable(self):
        self.assertTrue(triage.evaluate("open", ["valide", "bug"], False).workable)
        self.assertTrue(triage.evaluate("open", ["bug"], True).workable)

    def test_external_ticket_without_label_is_not_workable(self):
        self.assertFalse(triage.evaluate("open", ["bug"], False).workable)

    def test_closed_ticket_is_not_workable(self):
        self.assertFalse(triage.evaluate("closed", ["valide"], True).workable)


class GateCliTest(unittest.TestCase):
    def run_gate(self, gh, ref="essensys-hub/essensys-support#7"):
        out = io.StringIO()
        with redirect_stdout(out):
            code = triage_gate.main([ref, "--json"], runner=gh)
        return code, json.loads(out.getvalue())

    def test_report_from_bot_is_refused_with_code_3(self):
        code, data = self.run_gate(FakeGh(issue("essensys-support-bot[bot]", "Bot", ["a-valider"])))
        self.assertEqual(code, 3)
        self.assertFalse(data["workable"])

    def test_validated_report_is_accepted(self):
        code, _ = self.run_gate(FakeGh(issue("essensys-support-bot[bot]", "Bot", ["valide"])))
        self.assertEqual(code, 0)

    def test_maintainer_ticket_is_accepted_and_role_is_read(self):
        gh = FakeGh(issue("rhinosys"), roles={"rhinosys": "admin"})
        code, data = self.run_gate(gh)
        self.assertEqual((code, data["author_role"]), (0, "admin"))

    def test_non_collaborator_404_is_external(self):
        code, data = self.run_gate(FakeGh(issue("random-user")))
        self.assertEqual((code, data["author_role"]), (3, "none"))

    def test_read_error_fails_closed_with_code_2(self):
        code, data = self.run_gate(FakeGh(issue(), fail=True))
        self.assertEqual(code, 2)
        self.assertFalse(data["workable"])

    def test_url_reference(self):
        self.assertEqual(triage.parse_ref("https://github.com/essensys-hub/essensys-support/issues/12"),
                         ("essensys-hub/essensys-support", 12))
        with self.assertRaises(ValueError):
            triage.parse_ref("#12")


def event(action, *, sender=("rhinosys", "User"), author=("alice", "User"), labels=(), label=None, state="open"):
    ev = {"action": action, "issue": issue(author[0], author[1], labels, state),
          "sender": {"login": sender[0], "type": sender[1]}, "repository": {"full_name": "essensys-hub/essensys-support"}}
    if label:
        ev["label"] = {"name": label}
    return ev


class GuardDecideTest(unittest.TestCase):
    def ops(self, ev, sender_role="none", author_role="none"):
        return [(a.op, a.value) for a in triage_guard.decide(ev, sender_role=sender_role, author_role=author_role)]

    def test_external_issue_gets_a_valider_on_open(self):
        self.assertEqual(self.ops(event("opened", sender=("alice", "User"))), [("add_label", "a-valider")])
        self.assertEqual(self.ops(event("opened", author=("essensys-support-bot[bot]", "Bot"),
                                        sender=("essensys-support-bot[bot]", "Bot"), labels=["a-valider"])), [])

    def test_maintainer_issue_is_left_alone(self):
        self.assertEqual(self.ops(event("opened", author=("rhinosys", "User")), author_role="admin"), [])

    # NR: NR-lifecycle-4 essensys-hub/essensys-feature-lifecycle#18
    def test_valide_by_non_maintainer_is_removed_NR_lifecycle_4(self):
        for sender, role in ((("essensys-support-bot[bot]", "Bot"), "admin"), (("bob", "User"), "write")):
            ops = self.ops(event("labeled", sender=sender, labels=["valide"], label="valide"), sender_role=role)
            self.assertIn(("remove_label", "valide"), ops)
            self.assertTrue(any(op == "comment" for op, _ in ops))
            self.assertIn(("add_label", "a-valider"), ops)

    def test_valide_by_maintainer_clears_blocking_labels(self):
        ops = self.ops(event("labeled", labels=["valide", "a-valider", "besoin-info"], label="valide"),
                       sender_role="maintain")
        self.assertEqual(sorted(ops), [("remove_label", "a-valider"), ("remove_label", "besoin-info")])

    def test_removing_valide_puts_back_a_valider(self):
        self.assertEqual(self.ops(event("unlabeled", label="valide")), [("add_label", "a-valider")])
        self.assertEqual(self.ops(event("unlabeled", label="valide", state="closed")), [])

    def test_other_labels_are_ignored(self):
        self.assertEqual(self.ops(event("labeled", label="bug", sender=("bob", "User"))), [])

    def test_main_applies_actions_with_gh(self):
        ev = event("labeled", sender=("bob", "User"), labels=["valide"], label="valide")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(ev, handle)
        applied = []
        with redirect_stdout(io.StringIO()):
            triage_guard.main(["--event-path", handle.name, "--apply"],
                              json_runner=FakeGh({}, roles={"bob": "write"}), gh_runner=applied.append)
        self.assertIn(["issue", "edit", "7", "-R", "essensys-hub/essensys-support", "--remove-label", "valide"], applied)


class AdvanceRefusedTest(unittest.TestCase):
    # NR: NR-lifecycle-3 essensys-hub/essensys-feature-lifecycle#18
    def test_advance_refused_on_a_valider_NR_lifecycle_3(self):
        node = item_node("PVTI_1", "report-x-2026-10-009", "Idée")
        node["content"]["labels"] = {"nodes": [{"name": "a-valider"}]}
        runner = FakeRunner(items=[node])
        client = ps.GhClient(runner, dry_run=False, out=lambda _l: None)
        result = ps.advance(client, "report-x-2026-10-009", "spec-created")
        self.assertTrue(result.refused)
        self.assertIsNone(result.applied_status)
        self.assertEqual(runner.mutations(), [])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(ps.main(["advance", "report-x-2026-10-009", "spec-created", "--apply"], client=client), 3)

    def test_advance_still_works_without_blocking_label(self):
        runner = FakeRunner(items=[item_node("PVTI_1", "feat-x-2026-10-010", "Idée")])
        client = ps.GhClient(runner, dry_run=False, out=lambda _l: None)
        self.assertEqual(ps.advance(client, "feat-x-2026-10-010", "spec-created").applied_status, "Spec")


class ListWorkableTest(unittest.TestCase):
    def test_only_workable_tickets_are_listed(self):
        def item(n, author, utype, labels, state="OPEN", kind="Issue"):
            return {"id": f"I{n}", "fields": {"Status": "Idée"}, "content": {
                "type": kind, "number": n, "title": f"t{n}", "state": state, "repo": "essensys-hub/essensys-support",
                "labels": labels, "author": author, "author_type": utype}}
        items = [item(1, "essensys-support-bot", "Bot", ["a-valider"]), item(2, "essensys-support-bot", "Bot", ["valide"]),
                 item(3, "rhinosys", "User", []), item(4, "bob", "User", []), item(5, "rhinosys", "User", [], state="CLOSED"),
                 item(6, "rhinosys", "User", ["besoin-info"])]
        roles = {"rhinosys": "admin", "bob": "write"}
        workable, blocked = list_workable.classify(items, lambda _r, login, _t: roles.get(login, "none"))
        self.assertEqual([w["ref"] for w in workable], ["essensys-hub/essensys-support#2", "essensys-hub/essensys-support#3"])
        self.assertEqual(len(blocked), 3)


class SetupRepoTest(unittest.TestCase):
    def test_dry_run_writes_nothing_and_apply_creates_labels_and_caller(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            with redirect_stdout(io.StringIO()):
                setup_triage_repo.main(["essensys-hub/essensys-support", "--checkout", tmp], runner=lambda *a, **k: calls.append(a))
            self.assertEqual(calls, [])
            self.assertFalse((Path(tmp) / ".github/workflows/triage-guard.yml").exists())

            class Done:
                returncode = 0
            with redirect_stdout(io.StringIO()):
                setup_triage_repo.main(["essensys-hub/essensys-support", "--checkout", tmp, "--apply"],
                                       runner=lambda cmd, **k: calls.append(cmd) or Done())
            self.assertEqual(sorted(c[3] for c in calls), ["a-valider", "besoin-info", "valide"])
            caller = (Path(tmp) / ".github/workflows/triage-guard.yml").read_text(encoding="utf-8")
            self.assertIn("triage-guard.yml@main", caller)
            self.assertIn("issues: write", caller)

    def test_reusable_workflow_runs_guard_with_apply(self):
        wf = (Path(setup_triage_repo.__file__).resolve().parents[2] / ".github/workflows/triage-guard.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call", wf)
        self.assertIn("triage_guard.py", wf)
        self.assertIn("--apply", wf)


if __name__ == "__main__":
    unittest.main()
