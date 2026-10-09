#!/usr/bin/env python3
"""Synchronise feature lifecycle events and regression reports with the essensys-hub GitHub Project."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable


OWNER = os.environ.get("ESSENSYS_PROJECT_OWNER", "essensys-hub")
PROJECT_NUMBER = int(os.environ.get("ESSENSYS_PROJECT_NUMBER", "6"))

STATUS_FIELD = "Status"
FEATURE_ID_FIELD = "Feature ID"
STATUSES = ["Idée", "Spec", "Prêt", "En cours", "Test", "Gate sécu", "Déployé", "Archivé"]
EVENT_TARGETS = {
    "spec-created": "Spec",
    "ready": "Prêt",
    "pr-opened": "En cours",
    "all-prs-merged": "Test",
    "tests-passed": "Gate sécu",
    "deployed": "Déployé",
    "archived": "Archivé",
}
PR_EVENTS = ("pr-opened", "all-prs-merged")

FEATURE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
FEATURE_LINE_PATTERN = re.compile(r"^\s*feature\s*:\s*(\S+)\s*$", re.IGNORECASE | re.MULTILINE)
ISSUE_REF = r"(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#\d+"
CLOSES_PATTERN = re.compile(
    rf"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*:?\s+({ISSUE_REF})", re.IGNORECASE
)
REFS_PATTERN = re.compile(rf"\brefs?\s*:?\s+({ISSUE_REF})", re.IGNORECASE)
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
NR_MARKER_TEMPLATE = "<!-- nr:{nr_id} -->"
NR_MARKER_PATTERN = re.compile(r"<!--\s*nr:(NR-[a-z0-9-]+-\d+)\s*-->")
NR_ID_PATTERN = re.compile(r"NR-([a-z0-9-]+)-(\d+)")
ISSUE_REF_PARTS = re.compile(r"^(?:(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+))?#(?P<number>\d+)$")
FLAKY_ALTERNATIONS = 2
GREEN_STREAK_FOR_CLOSE = 3


# --------------------------------------------------------------------------- state machine


def status_index(status: str | None) -> int:
    """Index of a status in STATUSES; unknown/empty statuses sit before « Idée » (-1)."""
    if status and status in STATUSES:
        return STATUSES.index(status)
    return -1


def next_status(current: str | None, target: str) -> str | None:
    """Return target only when it moves the item forward; never regress automatically."""
    if target not in STATUSES:
        raise ValueError(f"Unknown target status: {target}")
    return target if STATUSES.index(target) > status_index(current) else None


# --------------------------------------------------------------------------- PR body parsing


@dataclass
class PrLinks:
    feature_id: str | None
    closes: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)

    @property
    def all_refs(self) -> list[str]:
        return self.closes + [ref for ref in self.refs if ref not in self.closes]


def _unique(items: list[str]) -> list[str]:
    seen: list[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen


def parse_pr_body(body: str | None) -> PrLinks:
    text = HTML_COMMENT_PATTERN.sub("", body or "")
    feature_id = None
    for match in FEATURE_LINE_PATTERN.finditer(text):
        candidate = match.group(1).strip("`*_")
        if FEATURE_ID_PATTERN.match(candidate):
            feature_id = candidate
            break
    closes = _unique([m.group(1) for m in CLOSES_PATTERN.finditer(text)])
    refs = _unique([m.group(1) for m in REFS_PATTERN.finditer(text)])
    return PrLinks(feature_id=feature_id, closes=closes, refs=refs)


def split_issue_ref(ref: str, default_repo: str | None = None) -> tuple[str | None, int]:
    """Split `owner/repo#12` or `#12` into (repo name or default, number)."""
    match = ISSUE_REF_PARTS.match(ref.strip())
    if not match:
        raise ValueError(f"Invalid issue reference: {ref}")
    return (match.group("repo") or default_repo, int(match.group("number")))


# --------------------------------------------------------------------------- GitHub client


class GhError(RuntimeError):
    pass


Runner = Callable[[str, dict[str, Any]], dict[str, Any]]


def gh_graphql_runner(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    """Run a GraphQL query through `gh api graphql` and return the parsed JSON payload."""
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if value is None:
            continue
        if isinstance(value, bool):
            cmd += ["-F", f"{key}={'true' if value else 'false'}"]
        elif isinstance(value, int):
            cmd += ["-F", f"{key}={value}"]
        elif isinstance(value, list):
            for item in value:
                cmd += ["-f", f"{key}[]={item}"]
        else:
            cmd += ["-f", f"{key}={value}"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise GhError(f"gh api graphql returned non-JSON output: {proc.stderr.strip()}") from exc
    if proc.returncode != 0 or payload.get("errors"):
        raise GhError(json.dumps(payload.get("errors")) if payload.get("errors") else proc.stderr.strip())
    return payload


PROJECT_QUERY = """
query($owner: String!, $number: Int!) {
  organization(login: $owner) {
    projectV2(number: $number) {
      id title url
      fields(first: 50) {
        nodes {
          ... on ProjectV2FieldCommon { id name dataType }
          ... on ProjectV2SingleSelectField { id name dataType options { id name } }
        }
      }
    }
  }
}
"""

ITEMS_QUERY = """
query($owner: String!, $number: Int!, $cursor: String) {
  organization(login: $owner) {
    projectV2(number: $number) {
      items(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          content {
            __typename
            ... on Issue { number title url state repository { nameWithOwner } issueType { name } }
            ... on PullRequest { number title url state repository { nameWithOwner } }
            ... on DraftIssue { title }
          }
          fieldValues(first: 30) {
            nodes {
              ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldNumberValue { number field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldDateValue { date field { ... on ProjectV2FieldCommon { name } } }
            }
          }
        }
      }
    }
  }
}
"""

ISSUE_ITEMS_QUERY = """
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      id number title url
      projectItems(first: 20) {
        nodes {
          id
          project { id number }
          fieldValues(first: 30) {
            nodes {
              ... on ProjectV2ItemFieldTextValue { text field { ... on ProjectV2FieldCommon { name } } }
              ... on ProjectV2ItemFieldSingleSelectValue { name field { ... on ProjectV2FieldCommon { name } } }
            }
          }
        }
      }
    }
  }
}
"""

REPO_META_QUERY = """
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    id
    labels(first: 100) { nodes { id name } }
    issueTypes(first: 20) { nodes { id name } }
  }
}
"""

ISSUE_ID_QUERY = """
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) { issue(number: $number) { id } }
}
"""

SEARCH_QUERY = """
query($q: String!) {
  search(query: $q, type: ISSUE, first: 100) {
    nodes {
      ... on Issue {
        number title body url state
        repository { name nameWithOwner }
        labels(first: 30) { nodes { name } }
      }
    }
  }
}
"""

SET_FIELD_MUTATION_SELECT = """
mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
  updateProjectV2ItemFieldValue(input: {projectId: $project, itemId: $item, fieldId: $field,
    value: {singleSelectOptionId: $option}}) { projectV2Item { id } }
}
"""

SET_FIELD_MUTATION_TEXT = """
mutation($project: ID!, $item: ID!, $field: ID!, $text: String!) {
  updateProjectV2ItemFieldValue(input: {projectId: $project, itemId: $item, fieldId: $field,
    value: {text: $text}}) { projectV2Item { id } }
}
"""

ADD_ITEM_MUTATION = """
mutation($project: ID!, $content: ID!) {
  addProjectV2ItemById(input: {projectId: $project, contentId: $content}) { item { id } }
}
"""

COMMENT_MUTATION = """
mutation($subject: ID!, $body: String!) {
  addComment(input: {subjectId: $subject, body: $body}) { commentEdge { node { url } } }
}
"""

CREATE_ISSUE_MUTATION = """
mutation($repo: ID!, $title: String!, $body: String!, $labels: [ID!], $type: ID) {
  createIssue(input: {repositoryId: $repo, title: $title, body: $body, labelIds: $labels,
    issueTypeId: $type}) { issue { id number url } }
}
"""

ADD_LABELS_MUTATION = """
mutation($labelable: ID!, $labels: [ID!]!) {
  addLabelsToLabelable(input: {labelableId: $labelable, labelIds: $labels}) { clientMutationId }
}
"""


def _field_values(nodes: list[dict[str, Any]] | None) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for node in nodes or []:
        if not node or not isinstance(node.get("field"), dict):
            continue
        name = node["field"].get("name")
        if not name:
            continue
        for key in ("text", "name", "number", "date"):
            if key in node:
                values[name] = node[key]
                break
    return values


def _normalize_item(node: dict[str, Any]) -> dict[str, Any]:
    content = node.get("content") or {}
    repo = (content.get("repository") or {}).get("nameWithOwner")
    return {
        "id": node.get("id"),
        "content": {
            "type": content.get("__typename"),
            "number": content.get("number"),
            "title": content.get("title"),
            "url": content.get("url"),
            "state": content.get("state"),
            "repo": repo,
            "issue_type": (content.get("issueType") or {}).get("name"),
        },
        "fields": _field_values((node.get("fieldValues") or {}).get("nodes")),
    }


class GhClient:
    """Thin GraphQL client for the org Project; writes are printed instead of sent in dry-run mode."""

    def __init__(
        self,
        runner: Runner | None = None,
        *,
        owner: str = OWNER,
        project_number: int = PROJECT_NUMBER,
        dry_run: bool = True,
        out: Callable[[str], None] = print,
    ) -> None:
        self.runner = runner or gh_graphql_runner
        self.owner = owner
        self.project_number = project_number
        self.dry_run = dry_run
        self.out = out
        self._project: dict[str, Any] | None = None
        self._repo_meta: dict[str, dict[str, Any]] = {}

    # -- plumbing

    def _query(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = self.runner(query, variables)
        if payload.get("errors"):
            raise GhError(json.dumps(payload["errors"]))
        return payload.get("data") or {}

    def _mutate(self, query: str, variables: dict[str, Any], dry_run: bool | None, label: str) -> dict[str, Any] | None:
        effective = self.dry_run if dry_run is None else dry_run
        if effective:
            self.out(f"[dry-run] {label}: {json.dumps(variables, ensure_ascii=False)}")
            return None
        return self._query(query, variables)

    # -- reads

    def project(self) -> dict[str, Any]:
        if self._project is None:
            data = self._query(PROJECT_QUERY, {"owner": self.owner, "number": self.project_number})
            raw = ((data.get("organization") or {}).get("projectV2")) or None
            if raw is None:
                raise GhError(f"Project {self.owner}#{self.project_number} not found")
            fields: dict[str, dict[str, Any]] = {}
            for node in (raw.get("fields") or {}).get("nodes") or []:
                if not node or not node.get("name"):
                    continue
                fields[node["name"]] = {
                    "id": node.get("id"),
                    "type": node.get("dataType"),
                    "options": {opt["name"]: opt["id"] for opt in node.get("options") or []},
                }
            self._project = {"id": raw["id"], "title": raw.get("title"), "url": raw.get("url"), "fields": fields}
        return self._project

    def iter_items(self, max_pages: int = 50):
        cursor: str | None = None
        for _ in range(max_pages):
            data = self._query(
                ITEMS_QUERY, {"owner": self.owner, "number": self.project_number, "cursor": cursor}
            )
            items = (((data.get("organization") or {}).get("projectV2") or {}).get("items")) or {}
            for node in items.get("nodes") or []:
                if node:
                    yield _normalize_item(node)
            page = items.get("pageInfo") or {}
            if not page.get("hasNextPage"):
                return
            cursor = page.get("endCursor")

    def find_item_by_feature_id(self, feature_id: str) -> dict[str, Any] | None:
        """Return the Feature item carrying this Feature ID (falls back to the first matching item)."""
        matches = [item for item in self.iter_items() if item["fields"].get(FEATURE_ID_FIELD) == feature_id]
        for item in matches:
            if item["content"].get("issue_type") == "Feature":
                return item
        return matches[0] if matches else None

    def item_for_issue(self, repo: str, number: int) -> dict[str, Any] | None:
        data = self._query(ISSUE_ITEMS_QUERY, {"owner": self.owner, "repo": repo, "number": number})
        issue = ((data.get("repository") or {}).get("issue")) or None
        if issue is None:
            return None
        for node in (issue.get("projectItems") or {}).get("nodes") or []:
            if node and (node.get("project") or {}).get("number") == self.project_number:
                return {
                    "id": node["id"],
                    "issue_id": issue.get("id"),
                    "content": {"number": issue.get("number"), "title": issue.get("title"), "url": issue.get("url"),
                                "repo": f"{self.owner}/{repo}"},
                    "fields": _field_values((node.get("fieldValues") or {}).get("nodes")),
                }
        return None

    def search_issues(self, query: str) -> list[dict[str, Any]]:
        data = self._query(SEARCH_QUERY, {"q": query})
        issues: list[dict[str, Any]] = []
        for node in (data.get("search") or {}).get("nodes") or []:
            if not node or "number" not in node:
                continue
            issues.append(
                {
                    "number": node["number"],
                    "title": node.get("title"),
                    "body": node.get("body") or "",
                    "url": node.get("url"),
                    "state": node.get("state"),
                    "repo": (node.get("repository") or {}).get("name"),
                    "labels": [label["name"] for label in (node.get("labels") or {}).get("nodes") or [] if label],
                }
            )
        return issues

    def _issue_id(self, repo: str, number: int) -> str:
        data = self._query(ISSUE_ID_QUERY, {"owner": self.owner, "repo": repo, "number": number})
        issue = ((data.get("repository") or {}).get("issue")) or None
        if not issue:
            raise GhError(f"Issue {self.owner}/{repo}#{number} not found")
        return issue["id"]

    def _repo(self, repo: str) -> dict[str, Any]:
        if repo not in self._repo_meta:
            data = self._query(REPO_META_QUERY, {"owner": self.owner, "repo": repo})
            raw = data.get("repository") or {}
            if not raw.get("id"):
                raise GhError(f"Repository {self.owner}/{repo} not found")
            self._repo_meta[repo] = {
                "id": raw["id"],
                "labels": {n["name"]: n["id"] for n in (raw.get("labels") or {}).get("nodes") or [] if n},
                "issue_types": {n["name"]: n["id"] for n in (raw.get("issueTypes") or {}).get("nodes") or [] if n},
            }
        return self._repo_meta[repo]

    def _field(self, field_name: str) -> dict[str, Any]:
        fields = self.project()["fields"]
        if field_name not in fields:
            raise GhError(f"Project field not found: {field_name}")
        return fields[field_name]

    # -- writes

    def set_single_select(self, item_id: str, field_name: str, option_name: str, *, dry_run: bool | None = None):
        fld = self._field(field_name)
        option_id = fld["options"].get(option_name)
        if option_id is None:
            raise GhError(f"Option {option_name!r} not found in field {field_name!r}")
        variables = {"project": self.project()["id"], "item": item_id, "field": fld["id"], "option": option_id}
        return self._mutate(SET_FIELD_MUTATION_SELECT, variables, dry_run, f"set {field_name}={option_name}")

    def set_text(self, item_id: str, field_name: str, value: str, *, dry_run: bool | None = None):
        fld = self._field(field_name)
        variables = {"project": self.project()["id"], "item": item_id, "field": fld["id"], "text": value}
        return self._mutate(SET_FIELD_MUTATION_TEXT, variables, dry_run, f"set {field_name}={value}")

    def add_issue(self, repo: str, number: int, *, dry_run: bool | None = None) -> str | None:
        variables = {"project": self.project()["id"], "content": self._issue_id(repo, number)}
        data = self._mutate(ADD_ITEM_MUTATION, variables, dry_run, f"add {repo}#{number} to project")
        return ((data or {}).get("addProjectV2ItemById") or {}).get("item", {}).get("id")

    def comment(self, repo: str, number: int, body: str, *, dry_run: bool | None = None):
        variables = {"subject": self._issue_id(repo, number), "body": body}
        return self._mutate(COMMENT_MUTATION, variables, dry_run, f"comment on {repo}#{number}")

    def add_labels(self, repo: str, number: int, labels: list[str], *, dry_run: bool | None = None):
        meta = self._repo(repo)
        label_ids = [meta["labels"][name] for name in labels if name in meta["labels"]]
        variables = {"labelable": self._issue_id(repo, number), "labels": label_ids}
        return self._mutate(ADD_LABELS_MUTATION, variables, dry_run, f"label {repo}#{number} {labels}")

    def create_issue(
        self, repo: str, title: str, body: str, labels: list[str], issue_type: str | None = None,
        *, dry_run: bool | None = None,
    ) -> dict[str, Any] | None:
        meta = self._repo(repo)
        variables = {
            "repo": meta["id"],
            "title": title,
            "body": body,
            "labels": [meta["labels"][name] for name in labels if name in meta["labels"]],
            "type": meta["issue_types"].get(issue_type) if issue_type else None,
        }
        data = self._mutate(CREATE_ISSUE_MUTATION, variables, dry_run, f"create issue in {repo}: {title}")
        return ((data or {}).get("createIssue") or {}).get("issue")


# --------------------------------------------------------------------------- lifecycle operations


@dataclass
class AdvanceResult:
    feature_id: str
    event: str
    item_id: str | None
    current: str | None
    target: str
    applied_status: str | None
    message: str


def advance(client: GhClient, feature_id: str, event: str, *, dry_run: bool | None = None) -> AdvanceResult:
    if event not in EVENT_TARGETS:
        raise ValueError(f"Unknown event {event!r}; expected one of {', '.join(EVENT_TARGETS)}")
    target = EVENT_TARGETS[event]
    item = client.find_item_by_feature_id(feature_id)
    if item is None:
        return AdvanceResult(feature_id, event, None, None, target, None,
                             f"No Project item carries Feature ID `{feature_id}`.")
    current = item["fields"].get(STATUS_FIELD)
    new_status = next_status(current, target)
    if new_status is None:
        return AdvanceResult(feature_id, event, item["id"], current, target, None,
                             f"Status kept at `{current}` (no automatic regression to `{target}`).")
    client.set_single_select(item["id"], STATUS_FIELD, new_status, dry_run=dry_run)
    return AdvanceResult(feature_id, event, item["id"], current, target, new_status,
                         f"Status `{current or '∅'}` → `{new_status}`.")


# --------------------------------------------------------------------------- regression tracking


@dataclass
class Action:
    kind: str  # open_bug | comment | add_label | propose_close
    nr_id: str
    repo: str | None
    number: int | None = None
    title: str | None = None
    body: str | None = None
    labels: list[str] = field(default_factory=list)


def count_alternations(history: list[str]) -> int:
    """Number of passed<->failed flips in a status history (skipped runs are ignored)."""
    relevant = [status for status in history if status in ("passed", "failed")]
    return sum(1 for prev, cur in zip(relevant, relevant[1:]) if prev != cur)


def is_flaky(history: list[str]) -> bool:
    return count_alternations(history) >= FLAKY_ALTERNATIONS


def trailing_passes(history: list[str]) -> int:
    count = 0
    for status in reversed(history):
        if status != "passed":
            break
        count += 1
    return count


def bug_marker(nr_id: str) -> str:
    return NR_MARKER_TEMPLATE.format(nr_id=nr_id)


def find_open_bug(nr_id: str, open_bugs: list[dict[str, Any]]) -> dict[str, Any] | None:
    marker = bug_marker(nr_id)
    for bug in open_bugs:
        if str(bug.get("state", "OPEN")).upper() != "OPEN":
            continue
        if marker in (bug.get("body") or ""):
            return bug
    return None


def repo_for_test(test: dict[str, Any]) -> str | None:
    """Target repo for a regression Bug: origin issue repo if explicit, else `essensys-<repo>` from the NR id."""
    issue = test.get("issue") or ""
    match = ISSUE_REF_PARTS.match(issue.strip()) if issue else None
    if match and match.group("repo"):
        return match.group("repo")
    nr = NR_ID_PATTERN.match(test.get("id") or "")
    if nr:
        slug = nr.group(1)
        return slug if slug.startswith("essensys-") else f"essensys-{slug}"
    return None


def _issue_link(issue: str | None, owner: str) -> str:
    if not issue:
        return "_inconnue_"
    match = ISSUE_REF_PARTS.match(issue.strip())
    if match and match.group("owner"):
        return f"{match.group('owner')}/{match.group('repo')}#{match.group('number')}"
    return issue


def regression_actions(report: dict[str, Any], open_bugs: list[dict[str, Any]], *, owner: str = OWNER) -> list[Action]:
    """Compute (pure) the GitHub actions a non-regression report implies. Never closes anything."""
    actions: list[Action] = []
    report_url = report.get("report_url") or report.get("url") or "_rapport non archivé_"
    for test in report.get("tests") or []:
        nr_id = test.get("id") or ""
        if not NR_ID_PATTERN.fullmatch(nr_id):
            continue
        status = test.get("status")
        history = list(test.get("history") or [status])
        flaky = is_flaky(history)
        bug = find_open_bug(nr_id, open_bugs)
        repo = (bug or {}).get("repo") or repo_for_test(test)
        name = test.get("name") or nr_id
        if status == "failed":
            if bug is None:
                labels = ["regression"] + (["flaky"] if flaky else [])
                body = "\n".join(
                    [
                        bug_marker(nr_id),
                        f"Le test de non-régression `{nr_id}` ({name}) échoue.",
                        "",
                        f"- Source : `{test.get('source', '?')}`",
                        f"- Rapport : {report_url}",
                        f"- Issue d'origine : {_issue_link(test.get('issue'), owner)}",
                        f"- Historique : {' → '.join(history)}",
                    ]
                )
                actions.append(Action("open_bug", nr_id, repo, title=f"[NR] {nr_id} : {name}", body=body, labels=labels))
            else:
                body = (
                    f"Nouvel échec de `{nr_id}` ({report.get('generated_at', 'date inconnue')}).\n\n"
                    f"- Rapport : {report_url}\n- Historique : {' → '.join(history)}"
                )
                actions.append(Action("comment", nr_id, repo, number=bug.get("number"), body=body))
        if bug is not None and flaky and "flaky" not in (bug.get("labels") or []):
            actions.append(Action("add_label", nr_id, repo, number=bug.get("number"), labels=["flaky"]))
        if status == "passed" and bug is not None and trailing_passes(history) == GREEN_STREAK_FOR_CLOSE:
            body = (
                f"`{nr_id}` est vert depuis {GREEN_STREAK_FOR_CLOSE} campagnes consécutives. "
                "Proposition de fermeture : à confirmer par un humain (pas de fermeture automatique).\n\n"
                f"- Rapport : {report_url}"
            )
            actions.append(Action("propose_close", nr_id, repo, number=bug.get("number"), body=body))
    return actions


def apply_actions(client: GhClient, actions: list[Action], *, dry_run: bool | None = None) -> list[str]:
    log: list[str] = []
    for action in actions:
        if not action.repo:
            log.append(f"SKIP {action.kind} {action.nr_id}: target repository unknown")
            continue
        if action.kind == "open_bug":
            issue = client.create_issue(action.repo, action.title or action.nr_id, action.body or "",
                                        action.labels, issue_type="Bug", dry_run=dry_run)
            if issue and issue.get("number"):
                item_id = client.add_issue(action.repo, issue["number"], dry_run=dry_run)
                if item_id:
                    client.set_single_select(item_id, STATUS_FIELD, "Idée", dry_run=dry_run)
            log.append(f"open_bug {action.repo}: {action.title}")
        elif action.kind in ("comment", "propose_close"):
            client.comment(action.repo, int(action.number or 0), action.body or "", dry_run=dry_run)
            log.append(f"{action.kind} {action.repo}#{action.number} ({action.nr_id})")
        elif action.kind == "add_label":
            client.add_labels(action.repo, int(action.number or 0), action.labels, dry_run=dry_run)
            log.append(f"add_label {action.repo}#{action.number} {action.labels}")
    return log


# --------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Sync feature lifecycle with GitHub Project {OWNER}#{PROJECT_NUMBER} (dry-run unless --apply)."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser("status", help="Show the Project item, status and fields of a feature.")
    status.add_argument("feature_id")

    adv = sub.add_parser("advance", help="Move a feature forward for a lifecycle event.")
    adv.add_argument("feature_id")
    adv.add_argument("event", choices=sorted(EVENT_TARGETS))
    adv.add_argument("--apply", action="store_true", help="Really write to GitHub (default: dry-run).")

    pr = sub.add_parser("pr-event", help="Advance the feature referenced by a PR body.")
    pr.add_argument("--pr-body-file", required=True)
    pr.add_argument("--event", required=True, choices=PR_EVENTS)
    pr.add_argument("--apply", action="store_true", help="Really write to GitHub (default: dry-run).")

    reg = sub.add_parser("regression", help="Open/comment regression Bugs from a nonreg report.")
    reg.add_argument("--report", required=True, help="JSON report produced by nonreg_report.py.")
    reg.add_argument("--report-url", help="Link to the archived report (overrides report_url in JSON).")
    reg.add_argument("--apply", action="store_true", help="Really write to GitHub (default: dry-run).")
    return parser


def write_github_step_summary(markdown: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write(markdown + "\n")


def _emit(args: argparse.Namespace, payload: dict[str, Any], markdown: str) -> None:
    write_github_step_summary(markdown)
    print(json.dumps(payload, indent=2, ensure_ascii=False) if args.json else markdown)


def main(argv: list[str] | None = None, client: GhClient | None = None) -> int:
    args = build_parser().parse_args(argv)
    apply = bool(getattr(args, "apply", False))
    client = client or GhClient(dry_run=not apply, out=lambda line: print(line, file=sys.stderr))
    mode = "apply" if apply else "dry-run"

    if args.command == "status":
        item = client.find_item_by_feature_id(args.feature_id)
        if item is None:
            _emit(args, {"feature_id": args.feature_id, "item": None},
                  f"# Feature `{args.feature_id}`\n\n- No Project item found.")
            return 1
        lines = [f"# Feature `{args.feature_id}`", "", f"- Item: `{item['id']}`",
                 f"- Issue: {item['content'].get('url') or item['content'].get('title')}",
                 f"- Status: `{item['fields'].get(STATUS_FIELD) or '∅'}`"]
        lines += [f"- {name}: `{value}`" for name, value in sorted(item["fields"].items()) if name != STATUS_FIELD]
        _emit(args, {"feature_id": args.feature_id, "item": item}, "\n".join(lines))
        return 0

    if args.command in ("advance", "pr-event"):
        if args.command == "pr-event":
            links = parse_pr_body(Path(args.pr_body_file).read_text(encoding="utf-8"))
            if not links.feature_id:
                _emit(args, {"ok": False, "error": "no Feature line"},
                      "# Project sync\n\n- PR body has no `Feature: <id>` line; nothing to sync.")
                return 0
            feature_id, event = links.feature_id, args.event
        else:
            feature_id, event = args.feature_id, args.event
        result = advance(client, feature_id, event)
        markdown = f"# Project sync ({mode})\n\n- Feature: `{feature_id}`\n- Event: `{event}`\n- {result.message}"
        _emit(args, {"mode": mode, **asdict(result)}, markdown)
        return 0

    if args.command == "regression":
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))
        if args.report_url:
            report["report_url"] = args.report_url
        open_bugs = client.search_issues(f"org:{client.owner} is:issue is:open label:regression")
        actions = regression_actions(report, open_bugs, owner=client.owner)
        log = apply_actions(client, actions)
        lines = [f"# Non-regression sync ({mode})", "", f"- Actions: `{len(actions)}`"]
        lines += [f"- {entry}" for entry in log] or ["- Nothing to do."]
        _emit(args, {"mode": mode, "actions": [asdict(a) for a in actions], "log": log}, "\n".join(lines))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
