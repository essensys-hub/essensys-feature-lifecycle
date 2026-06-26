#!/usr/bin/env python3
"""Create, update, promote, or delete Confluence pages linked from feature manifests."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import markdown
import requests


REPO_ROOT = Path(__file__).resolve().parents[2]
API_ROOT = "https://api.atlassian.com/ex/confluence/{cloud_id}/wiki/rest/api"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    draft = sub.add_parser("draft", help="Create or update a draft page from a manifest.")
    draft.add_argument("--manifest", required=True)
    draft.add_argument("--pr-number", required=False)
    draft.add_argument("--branch", required=False)

    promote = sub.add_parser("promote", help="Promote a draft page after merge.")
    promote.add_argument("--manifest", required=True)

    delete = sub.add_parser("delete-draft", help="Delete an abandoned draft page.")
    delete.add_argument("--manifest", required=True)

    return parser


class ConfluenceClient:
    def __init__(self, account: str, token: str, cloud_id: str) -> None:
        self.base_url = API_ROOT.format(cloud_id=cloud_id)
        self.session = requests.Session()
        self.session.auth = (account, token)
        self.session.headers.update({"Accept": "application/json"})

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        response = self.session.request(
            method,
            f"{self.base_url}{path}",
            timeout=60,
            **kwargs,
        )
        response.raise_for_status()
        return response

    def get_page(self, page_id: str) -> dict[str, object]:
        return self.request("GET", f"/content/{page_id}?expand=version,body.storage").json()

    def create_page(self, *, title: str, space_key: str, parent_page_id: str, body_html: str) -> str:
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "ancestors": [{"id": parent_page_id}],
            "body": {
                "storage": {
                    "value": body_html,
                    "representation": "storage",
                }
            },
        }
        data = self.request("POST", "/content", json=payload).json()
        return str(data["id"])

    def update_page(self, *, page_id: str, title: str, body_html: str) -> str:
        current = self.get_page(page_id)
        version = int(current["version"]["number"]) + 1
        payload = {
          "id": page_id,
          "type": "page",
          "title": title,
          "version": {"number": version},
          "body": {
              "storage": {
                  "value": body_html,
                  "representation": "storage",
              }
          },
        }
        data = self.request("PUT", f"/content/{page_id}", json=payload).json()
        return str(data["id"])

    def delete_page(self, page_id: str) -> None:
        self.request("DELETE", f"/content/{page_id}")


def load_manifest(path_str: str) -> tuple[Path, dict[str, object]]:
    path = (REPO_ROOT / path_str).resolve() if not Path(path_str).is_absolute() else Path(path_str)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return path, payload


def save_manifest(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_storage(markdown_path: Path, manifest: dict[str, object], *, draft: bool, pr_number: str | None, branch: str | None) -> str:
    content = markdown_path.read_text(encoding="utf-8")
    html = markdown.markdown(
        content,
        extensions=["fenced_code", "tables", "toc"],
    )
    badges = []
    if draft:
        badges.append("<p><strong>Status:</strong> Draft generated from pull request automation.</p>")
    if pr_number:
        badges.append(f"<p><strong>PR:</strong> #{pr_number}</p>")
    if branch:
        badges.append(f"<p><strong>Branch:</strong> {branch}</p>")
    badges.append(f"<p><strong>Feature id:</strong> {manifest['id']}</p>")
    return "\n".join(badges + [html])


def build_client() -> ConfluenceClient:
    account = os.environ.get("CONFLUENCE_ACCOUNT", "")
    token = os.environ.get("CONFLUENCE_TOKEN", "")
    cloud_id = os.environ.get("CONFLUENCE_CLOUD_ID", "")
    missing = [name for name, value in {
        "CONFLUENCE_ACCOUNT": account,
        "CONFLUENCE_TOKEN": token,
        "CONFLUENCE_CLOUD_ID": cloud_id,
    }.items() if not value]
    if missing:
        raise SystemExit(f"Missing Confluence env vars: {', '.join(missing)}")
    return ConfluenceClient(account=account, token=token, cloud_id=cloud_id)


def userguide_page(manifest: dict[str, object]) -> Path:
    pages = manifest.get("userguide", {}).get("pages", [])
    if not pages:
        raise SystemExit("Manifest has no user guide pages.")
    return REPO_ROOT / pages[0]


def draft_title(title: str) -> str:
    return title if title.startswith("[DRAFT] ") else f"[DRAFT] {title}"


def published_title(title: str) -> str:
    return title.removeprefix("[DRAFT] ")


def cmd_draft(args: argparse.Namespace) -> int:
    manifest_path, manifest = load_manifest(args.manifest)
    page_path = userguide_page(manifest)
    if not page_path.exists():
        print("SKIP")
        return 0
    client = build_client()
    body = build_storage(page_path, manifest, draft=True, pr_number=args.pr_number, branch=args.branch)
    config = manifest["confluence"]
    title = draft_title(str(manifest["title"]))
    draft_page_id = config.get("draft_page_id")
    if draft_page_id:
        page_id = client.update_page(page_id=str(draft_page_id), title=title, body_html=body)
    else:
        page_id = client.create_page(
            title=title,
            space_key=str(config["space"]),
            parent_page_id=str(config["parent_page"]),
            body_html=body,
        )
    manifest["confluence"]["draft_page_id"] = page_id
    save_manifest(manifest_path, manifest)
    print(page_id)
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    manifest_path, manifest = load_manifest(args.manifest)
    page_path = userguide_page(manifest)
    if not page_path.exists():
        print("SKIP")
        return 0
    client = build_client()
    config = manifest["confluence"]
    page_id = str(config.get("draft_page_id") or config.get("published_page_id") or "")
    if not page_id:
        body = build_storage(page_path, manifest, draft=False, pr_number=None, branch=None)
        page_id = client.create_page(
            title=published_title(str(manifest["title"])),
            space_key=str(config["space"]),
            parent_page_id=str(config["parent_page"]),
            body_html=body,
        )
    else:
        body = build_storage(page_path, manifest, draft=False, pr_number=None, branch=None)
        client.update_page(page_id=page_id, title=published_title(str(manifest["title"])), body_html=body)
    manifest["confluence"]["published_page_id"] = page_id
    save_manifest(manifest_path, manifest)
    print(page_id)
    return 0


def cmd_delete_draft(args: argparse.Namespace) -> int:
    manifest_path, manifest = load_manifest(args.manifest)
    draft_page_id = manifest.get("confluence", {}).get("draft_page_id")
    if not draft_page_id:
        return 0
    client = build_client()
    client.delete_page(str(draft_page_id))
    manifest["confluence"]["draft_page_id"] = None
    save_manifest(manifest_path, manifest)
    return 0


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "draft":
        return cmd_draft(args)
    if args.command == "promote":
        return cmd_promote(args)
    if args.command == "delete-draft":
        return cmd_delete_draft(args)
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
