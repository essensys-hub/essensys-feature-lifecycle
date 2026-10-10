"""Règles de tri des tickets venus de l'extérieur (report-triage-2026-10-005).

Un ticket est « exploitable » par Claude seulement s'il porte `valide`, ou s'il a été
ouvert par un mainteneur sans label de tri bloquant. Tout le reste est en lecture seule.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from typing import Any, Callable

A_VALIDER = "a-valider"
VALIDE = "valide"
BESOIN_INFO = "besoin-info"
TRIAGE_LABELS = (A_VALIDER, VALIDE, BESOIN_INFO)
BLOCKING_LABELS = (A_VALIDER, BESOIN_INFO)
MAINTAINER_ROLES = {"maintain", "admin"}

EXIT_WORKABLE = 0
EXIT_READ_ERROR = 2
EXIT_NOT_WORKABLE = 3


def is_bot(login: str | None, user_type: str | None) -> bool:
    return (user_type or "").lower() == "bot" or (login or "").endswith("[bot]")


def is_maintainer(login: str | None, user_type: str | None, role: str | None) -> bool:
    """Rôle `maintain` ou `admin` sur le dépôt (donné par l'équipe maintainers) ; jamais un bot."""
    if not login or is_bot(login, user_type):
        return False
    return (role or "").lower() in MAINTAINER_ROLES


@dataclass
class Verdict:
    workable: bool
    reason: str
    action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate(state: str, labels: list[str], author_is_maintainer: bool) -> Verdict:
    """Règle « exploitable » de la spec report-triage."""
    names = {label.lower() for label in labels}
    if (state or "").lower() != "open":
        return Verdict(False, "le ticket est fermé", "rouvrir le ticket si du travail reste à faire")
    blocking = [label for label in BLOCKING_LABELS if label in names]
    if blocking:
        return Verdict(False, f"le ticket porte `{blocking[0]}`",
                       "un mainteneur doit relire le ticket et poser `valide` (ou fournir les informations manquantes)")
    if VALIDE in names:
        return Verdict(True, "validé par un mainteneur (`valide`)")
    if author_is_maintainer:
        return Verdict(True, "ouvert par un mainteneur")
    return Verdict(False, "ouvert par une personne extérieure et pas encore validé",
                   "un mainteneur doit relire le ticket et poser `valide`")


# --------------------------------------------------------------------------- lecture GitHub

class ReadError(RuntimeError):
    pass


JsonRunner = Callable[[list[str]], Any]


def gh_json(args: list[str]) -> Any:
    proc = subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise ReadError((proc.stderr or proc.stdout).strip()[:300])
    return json.loads(proc.stdout or "null")


def author_role(repo: str, login: str, user_type: str | None, runner: JsonRunner = gh_json) -> str:
    """Rôle de l'auteur sur le dépôt ; « none » pour un bot ou un non-collaborateur."""
    if is_bot(login, user_type):
        return "none"
    try:
        data = runner([f"repos/{repo}/collaborators/{login}/permission"])
    except ReadError as exc:
        if "404" in str(exc) or "Not Found" in str(exc) or "is not a user" in str(exc):
            return "none"
        raise
    return (data or {}).get("role_name") or (data or {}).get("permission") or "none"


def parse_ref(ref: str) -> tuple[str, int]:
    """`owner/repo#n` ou URL d'issue → (owner/repo, n)."""
    ref = ref.strip()
    if ref.startswith("http"):
        parts = ref.rstrip("/").split("/")
        if len(parts) >= 7 and parts[-2] in ("issues", "pull"):
            return f"{parts[-4]}/{parts[-3]}", int(parts[-1])
        raise ValueError(f"URL d'issue non reconnue : {ref}")
    if "#" not in ref or "/" not in ref.split("#")[0]:
        raise ValueError(f"Référence attendue owner/repo#n : {ref}")
    repo, number = ref.split("#", 1)
    return repo, int(number)


def check(ref: str, runner: JsonRunner = gh_json) -> tuple[dict[str, Any], Verdict]:
    """Lit l'issue et rend le verdict. Lève ReadError si GitHub ne répond pas (fail-closed côté appelant)."""
    repo, number = parse_ref(ref)
    issue = runner([f"repos/{repo}/issues/{number}"])
    user = issue.get("user") or {}
    labels = [label.get("name", "") for label in issue.get("labels") or []]
    role = author_role(repo, user.get("login", ""), user.get("type"), runner)
    maintainer = is_maintainer(user.get("login"), user.get("type"), role)
    info = {"ref": f"{repo}#{number}", "state": issue.get("state"), "labels": labels,
            "author": user.get("login"), "author_type": user.get("type"), "author_role": role}
    return info, evaluate(issue.get("state", ""), labels, maintainer)
