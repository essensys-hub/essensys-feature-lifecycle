"""Shared helpers for feature lifecycle script tests (no network, no gh)."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def item_node(item_id, feature_id, status, issue_type="Feature", number=1):
    values = [{"text": feature_id, "field": {"name": "Feature ID"}}]
    if status is not None:
        values.append({"name": status, "field": {"name": "Status"}})
    return {
        "id": item_id,
        "content": {
            "__typename": "Issue",
            "number": number,
            "title": f"{feature_id} issue",
            "url": f"https://github.com/essensys-hub/essensys-feature-lifecycle/issues/{number}",
            "state": "OPEN",
            "repository": {"nameWithOwner": "essensys-hub/essensys-feature-lifecycle"},
            "issueType": {"name": issue_type},
        },
        "fieldValues": {"nodes": values},
    }


class FakeRunner:
    """Records every GraphQL call and answers from canned data; fails loudly on unknown queries."""

    def __init__(self, items=None, search=None):
        self.calls = []
        self.items = items or []
        self.search = search or []

    def __call__(self, query, variables):
        self.calls.append((query, dict(variables)))
        if "mutation" in query:
            if "createIssue" in query:
                return {"data": {"createIssue": {"issue": {"id": "I_new", "number": 101, "url": "u"}}}}
            if "addProjectV2ItemById" in query:
                return {"data": {"addProjectV2ItemById": {"item": {"id": "PVTI_new"}}}}
            return {"data": {"ok": True}}
        if "fields(first" in query:
            return {"data": {"organization": {"projectV2": {
                "id": "PVT_1", "title": "Essensys Roadmap", "url": "u",
                "fields": {"nodes": [
                    {"id": "F_status", "name": "Status", "dataType": "SINGLE_SELECT",
                     "options": [{"id": f"O_{i}", "name": n} for i, n in enumerate(
                         ["Idée", "Spec", "Prêt", "En cours", "Test", "Gate sécu", "Déployé", "Archivé"])]},
                    {"id": "F_fid", "name": "Feature ID", "dataType": "TEXT"},
                    {"id": "F_title", "name": "Title", "dataType": "TITLE"},
                ]},
            }}}}
        if "items(first" in query:
            return {"data": {"organization": {"projectV2": {"items": {
                "pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": self.items}}}}}
        if "search(query" in query:
            return {"data": {"search": {"nodes": self.search}}}
        if "labels(first: 100)" in query:
            return {"data": {"repository": {
                "id": "R_1",
                "labels": {"nodes": [{"id": "L_reg", "name": "regression"}, {"id": "L_flaky", "name": "flaky"}]},
                "issueTypes": {"nodes": [{"id": "T_bug", "name": "Bug"}]},
            }}}
        if "projectItems" in query:
            return {"data": {"repository": {"issue": {
                "id": "I_x", "number": variables["number"], "title": "t", "url": "u",
                "projectItems": {"nodes": [{"id": "PVTI_issue", "project": {"id": "PVT_1", "number": 6},
                                            "fieldValues": {"nodes": [{"name": "Test", "field": {"name": "Status"}}]}}]},
            }}}}
        if "issue(number" in query:
            return {"data": {"repository": {"issue": {"id": f"I_{variables['number']}"}}}}
        raise AssertionError(f"Unexpected query: {query[:80]}")

    def mutations(self):
        return [(q, v) for q, v in self.calls if "mutation" in q]
