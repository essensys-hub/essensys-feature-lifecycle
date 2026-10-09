#!/usr/bin/env python3
"""Configure the Essensys GitHub Project (title, Status options, custom fields) idempotently."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass


OWNER = os.environ.get("ESSENSYS_PROJECT_OWNER", "essensys-hub")
PROJECT_NUMBER = int(os.environ.get("ESSENSYS_PROJECT_NUMBER", "6"))
TITLE = "Essensys Roadmap"
DESCRIPTION = (
    "Pilotage unique du cycle de vie Essensys : tickets, features, non-régression. "
    "Gouvernance : essensys-feature-lifecycle/claude/GOVERNANCE.md"
)

STATUS_OPTIONS = [
    ("Idée", "GRAY", "Ticket créé, à qualifier"),
    ("Spec", "BLUE", "Change OpenSpec en cours"),
    ("Prêt", "PURPLE", "Spec validée, sub-issues créées"),
    ("En cours", "YELLOW", "Au moins une PR liée ouverte"),
    ("Test", "ORANGE", "PR mergées, tests applicatifs en cours"),
    ("Gate sécu", "PINK", "Tests verts, gate sécurité / deploy en attente"),
    ("Déployé", "GREEN", "Déployé en local et sur OVH"),
    ("Archivé", "GRAY", "Change OpenSpec archivé, mémoire mise à jour"),
]

SINGLE_SELECT_FIELDS = {
    "Phase": [
        ("0 doc/install", "GRAY", ""),
        ("1", "BLUE", ""),
        ("2", "PURPLE", ""),
        ("3", "PINK", ""),
    ],
    "Cible": [
        ("gateway", "BLUE", "Gateway locale / Raspberry"),
        ("cloud", "PURPLE", "Portail OVH / mon.essensys.fr"),
        ("firmware", "ORANGE", "Cartes SC9xx"),
        ("mobile", "GREEN", "Apps Android / iOS"),
        ("infra", "GRAY", "Ansible, proxy, CI"),
        ("doc", "YELLOW", "Documentation, support-site"),
    ],
}
TEXT_FIELDS = ["Feature ID", "Appareil"]


@dataclass
class Step:
    description: str
    query: str
    variables: dict[str, object]


def gh_graphql(query: str, variables: dict[str, object] | None = None) -> dict[str, object]:
    payload = json.dumps({"query": query, "variables": variables or {}})
    completed = subprocess.run(
        ["gh", "api", "graphql", "--input", "-"],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    data = json.loads(completed.stdout)
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], ensure_ascii=False))
    return data["data"]


PROJECT_QUERY = """
query($owner: String!, $number: Int!) {
  organization(login: $owner) {
    projectV2(number: $number) {
      id
      title
      shortDescription
      fields(first: 50) {
        nodes {
          __typename
          ... on ProjectV2FieldCommon { id name dataType }
          ... on ProjectV2SingleSelectField { options { id name color description } }
        }
      }
    }
  }
}
"""


def options_input(options: list[tuple[str, str, str]]) -> list[dict[str, str]]:
    return [{"name": name, "color": color, "description": desc} for name, color, desc in options]


def plan(project: dict[str, object]) -> list[Step]:
    steps: list[Step] = []
    project_id = project["id"]
    fields = {field["name"]: field for field in project["fields"]["nodes"] if field.get("name")}

    if project["title"] != TITLE or project.get("shortDescription") != DESCRIPTION:
        steps.append(
            Step(
                f"Renommer le Project « {project['title']} » → « {TITLE} »",
                """mutation($id: ID!, $title: String!, $desc: String!) {
                  updateProjectV2(input: {projectId: $id, title: $title, shortDescription: $desc}) { projectV2 { id } }
                }""",
                {"id": project_id, "title": TITLE, "desc": DESCRIPTION},
            )
        )

    status = fields.get("Status")
    wanted = [name for name, _, _ in STATUS_OPTIONS]
    current = [option["name"] for option in (status or {}).get("options", [])]
    if status and current != wanted:
        steps.append(
            Step(
                f"Status : {current} → {wanted}",
                """mutation($id: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]) {
                  updateProjectV2Field(input: {fieldId: $id, singleSelectOptions: $options}) { projectV2Field { ... on ProjectV2SingleSelectField { id } } }
                }""",
                {"id": status["id"], "options": options_input(STATUS_OPTIONS)},
            )
        )

    for name, options in SINGLE_SELECT_FIELDS.items():
        existing = fields.get(name)
        if existing is None:
            steps.append(
                Step(
                    f"Créer le champ single select « {name} » {[o[0] for o in options]}",
                    """mutation($project: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]) {
                      createProjectV2Field(input: {projectId: $project, dataType: SINGLE_SELECT, name: $name, singleSelectOptions: $options}) { projectV2Field { ... on ProjectV2SingleSelectField { id } } }
                    }""",
                    {"project": project_id, "name": name, "options": options_input(options)},
                )
            )
        elif [o["name"] for o in existing.get("options", [])] != [o[0] for o in options]:
            steps.append(
                Step(
                    f"Mettre à jour les options de « {name} »",
                    """mutation($id: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]) {
                      updateProjectV2Field(input: {fieldId: $id, singleSelectOptions: $options}) { projectV2Field { ... on ProjectV2SingleSelectField { id } } }
                    }""",
                    {"id": existing["id"], "options": options_input(options)},
                )
            )

    for name in TEXT_FIELDS:
        if name not in fields:
            steps.append(
                Step(
                    f"Créer le champ texte « {name} »",
                    """mutation($project: ID!, $name: String!) {
                      createProjectV2Field(input: {projectId: $project, dataType: TEXT, name: $name}) { projectV2Field { ... on ProjectV2Field { id } } }
                    }""",
                    {"project": project_id, "name": name},
                )
            )
    return steps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Exécuter les mutations (défaut : dry-run).")
    args = parser.parse_args()

    data = gh_graphql(PROJECT_QUERY, {"owner": OWNER, "number": PROJECT_NUMBER})
    project = data["organization"]["projectV2"]
    if project is None:
        print(f"Project #{PROJECT_NUMBER} introuvable pour {OWNER}", file=sys.stderr)
        return 2

    steps = plan(project)
    print(f"Project {OWNER}#{PROJECT_NUMBER} « {project['title']} » : {len(steps)} changement(s)")
    for step in steps:
        prefix = "APPLY" if args.apply else "dry-run"
        print(f"  [{prefix}] {step.description}")
        if args.apply:
            gh_graphql(step.query, step.variables)
    if not steps:
        print("  Déjà conforme.")
    elif not args.apply:
        print("Relancer avec --apply pour appliquer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
