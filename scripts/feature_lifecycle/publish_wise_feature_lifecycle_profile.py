#!/usr/bin/env python3
"""Publish local lifecycle artifacts, then create/update the team profile."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path

import requests


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ArtifactSpec:
    name: str
    artifact_type: str
    source_path: str
    description: str
    publish: bool = True
    include_in_profile: bool = True


LOCAL_ARTIFACTS: list[ArtifactSpec] = [
    ArtifactSpec(
        name="feature-manifest-orchestrator",
        artifact_type="skill",
        source_path=".cursor/skills/feature-manifest-orchestrator",
        description="Create and validate feature manifests from Jira and OpenSpec.",
    ),
    ArtifactSpec(
        name="feature-userguide-sync",
        artifact_type="skill",
        source_path=".cursor/skills/feature-userguide-sync",
        description="Sync feature user guides from manifests and code.",
    ),
    ArtifactSpec(
        name="playwright-from-spec",
        artifact_type="skill",
        source_path=".cursor/skills/playwright-from-spec",
        description="Generate Playwright specs from manifests and OpenSpec.",
    ),
    ArtifactSpec(
        name="feature-lifecycle-bootstrap",
        artifact_type="skill",
        source_path=".cursor/skills/feature-lifecycle-bootstrap",
        description="Bootstrap the feature lifecycle in empty or existing repositories.",
    ),
    ArtifactSpec(
        name="security-gate-triage",
        artifact_type="skill",
        source_path=".cursor/skills/security-gate-triage",
        description="Triage secrets, CVEs, lint security findings, and Dependabot alerts.",
    ),
    ArtifactSpec(
        name="jira-xray-test-campaign",
        artifact_type="skill",
        source_path=".cursor/skills/jira-xray-test-campaign",
        description="Create and maintain Jira / Xray test campaigns.",
    ),
    ArtifactSpec(
        name="openspec-explore",
        artifact_type="skill",
        source_path=".cursor/skills/openspec-explore",
        description="Explore feature requirements before implementing an OpenSpec change.",
    ),
    ArtifactSpec(
        name="openspec-propose",
        artifact_type="skill",
        source_path=".cursor/skills/openspec-propose",
        description="Propose a new OpenSpec change with its initial artifacts.",
    ),
    ArtifactSpec(
        name="openspec-apply-change",
        artifact_type="skill",
        source_path=".cursor/skills/openspec-apply-change",
        description="Implement tasks from an OpenSpec change.",
    ),
    ArtifactSpec(
        name="openspec-archive-change",
        artifact_type="skill",
        source_path=".cursor/skills/openspec-archive-change",
        description="Archive a completed OpenSpec change.",
    ),
    ArtifactSpec(
        name="software-architecture",
        artifact_type="skill",
        source_path=".cursor/skills/software-architecture",
        description="Quality-focused software architecture guidance.",
    ),
    ArtifactSpec(
        name="angular-architect",
        artifact_type="skill",
        source_path=".cursor/skills/angular-architect",
        description="Angular architecture guidance for enterprise projects.",
    ),
    ArtifactSpec(
        name="gxp-unit-test-report-generator",
        artifact_type="skill",
        source_path=".cursor/skills/gxp-unit-test-report-generator",
        description="Generate audit-ready unit test reports.",
    ),
    ArtifactSpec(
        name="dry-run-install-procedure",
        artifact_type="skill",
        source_path=".cursor/skills/dry-run-install-procedure",
        description="Write ultra-detailed dry-run Installation Procedure docs paired with GxP install procedures.",
    ),
    ArtifactSpec(
        name="playwright-ui-tests",
        artifact_type="rule",
        source_path=".cursor/rules/playwright-ui-tests.mdc",
        description="Project rule for robust Playwright UI tests.",
    ),
    ArtifactSpec(
        name="release-changelog-auto",
        artifact_type="rule",
        source_path=".cursor/rules/release-changelog-auto.mdc",
        description="Project rule for changelog updates.",
    ),
    ArtifactSpec(
        name="github-issue-done-commit-push",
        artifact_type="rule",
        source_path=".cursor/rules/github-issue-done-commit-push.mdc",
        description="Project rule for GitHub issue lifecycle discipline.",
    ),
    ArtifactSpec(
        name="language",
        artifact_type="rule",
        source_path=".cursor/rules/language.mdc",
        description="Project rule for assistant language in this repository.",
    ),
    ArtifactSpec(
        name="security-gate",
        artifact_type="rule",
        source_path=".cursor/rules/security-gate.mdc",
        description="Project rule for secrets, CVEs, Dockerfiles, and workflows.",
    ),
    ArtifactSpec(
        name="gxp-exec",
        artifact_type="rule",
        source_path=".cursor/rules/gxp-exec.mdc",
        description="Project rule for GxP execution: documented/automated dry-run, deviations on pre-requisites and run/install.",
    ),
    ArtifactSpec(
        name="dry-run-install-doc",
        artifact_type="rule",
        source_path=".cursor/rules/dry-run-install-doc.mdc",
        description="Keep dry-run install procedure docs in sync and at required detail level.",
    ),
]

EXTERNAL_PROFILE_ITEMS = [
    {"artifact_type": "skill", "artifact_name": "confluence-page-generator", "version_selector": "latest", "tool_scope": "cursor"},
    {"artifact_type": "skill", "artifact_name": "git-secret-cleaner", "version_selector": "latest", "tool_scope": "cursor"},
]

OPTIONAL_PROFILE_ITEMS = [
    {"artifact_type": "mcp", "artifact_name": "atlassian", "version_selector": "latest", "tool_scope": "cursor"},
    {"artifact_type": "mcp", "artifact_name": "github", "version_selector": "latest", "tool_scope": "cursor"},
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--team-id", type=int, default=2)
    parser.add_argument(
        "--owner-user-id-2",
        default="i0438973",
        help="Second profile owner, allowed to edit the profile from the admin UI.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def api_request(
    session: requests.Session,
    method: str,
    url: str,
    *,
    expected: tuple[int, ...] = (200,),
    **kwargs,
) -> requests.Response:
    response = session.request(method, url, timeout=120, **kwargs)
    if response.status_code not in expected:
        raise SystemExit(f"{method} {url} failed: {response.status_code} {response.text}")
    return response


def load_artifact(spec: ArtifactSpec) -> dict[str, object]:
    source = REPO_ROOT / spec.source_path
    if spec.artifact_type in {"skill"}:
        main_path = source / "SKILL.md"
        if not main_path.exists():
            raise SystemExit(f"Missing SKILL.md for {spec.name}: {main_path}")
        files: dict[str, str] = {}
        for path in sorted(source.rglob("*")):
            if path.is_dir() or path == main_path:
                continue
            rel_path = str(path.relative_to(source))
            try:
                files[rel_path] = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
        content = main_path.read_text(encoding="utf-8")
    else:
        content = source.read_text(encoding="utf-8")
        files = {}

    return {
        "name": spec.name,
        "artifact_type": spec.artifact_type,
        "version": None,
        "description": spec.description,
        "changelog": "Official publication for the wise-feature-lifecycle profile.",
        "content": content,
        "files": files,
        "source_repo": "essensys-hub/essensys-feature-lifecycle",
        "actor": "wise-feature-lifecycle",
    }


def try_resolve_artifact_id(
    session: requests.Session,
    api_url: str,
    name: str,
    artifact_type: str,
) -> int | None:
    response = session.get(
        f"{api_url}/api/skills",
        params={"q": name, "context": "admin"},
        timeout=120,
    )
    if response.status_code != 200:
        return None
    for item in response.json().get("items", []):
        if item.get("name") == name and item.get("artifact_type") == artifact_type:
            return int(item["id"])
    return None


def resolve_artifact_id(
    session: requests.Session,
    api_url: str,
    name: str,
    artifact_type: str,
) -> int:
    response = api_request(
        session,
        "GET",
        f"{api_url}/api/skills",
        params={"q": name, "context": "admin"},
    )
    for item in response.json().get("items", []):
        if item.get("name") == name and item.get("artifact_type") == artifact_type:
            return int(item["id"])
    raise SystemExit(f"Artifact not found after publish: {artifact_type} {name}")


def version_entry(
    session: requests.Session,
    api_url: str,
    artifact_id: int,
    version: str,
) -> dict | None:
    response = api_request(
        session,
        "GET",
        f"{api_url}/api/skills/{artifact_id}/versions",
        params={"context": "admin"},
    )
    for entry in response.json().get("items", []):
        if str(entry.get("version")) == version:
            return entry
    return None


def resolve_version_id(
    session: requests.Session,
    api_url: str,
    artifact_id: int,
    version: str,
) -> int | None:
    entry = version_entry(session, api_url, artifact_id, version)
    return int(entry["id"]) if entry is not None else None


def approve_artifact_version(
    session: requests.Session,
    api_url: str,
    artifact_id: int,
    version_id: int,
    name: str,
) -> bool:
    response = session.post(
        f"{api_url}/api/skills/{artifact_id}/versions/{version_id}/approve-by-human",
        timeout=120,
    )
    if response.status_code in (200, 201):
        print(f"[ok] approved {name} by human override")
        return True
    print(
        f"[warn] approve-by-human for {name} returned "
        f"{response.status_code}: {response.text[:200]}"
    )
    return False


def version_needs_reupload(entry: dict | None) -> bool:
    if entry is None:
        return True
    if entry.get("is_published"):
        return False
    status = str(entry.get("verification_status") or "").upper()
    return status in {"ERROR", "REJECTED"} or not status


def publish_artifact_version(
    session: requests.Session,
    api_url: str,
    spec: ArtifactSpec,
    version: str,
    *,
    dry_run: bool,
) -> None:
    if not spec.publish:
        return

    artifact_id = resolve_artifact_id(session, api_url, spec.name, spec.artifact_type)
    entry = version_entry(session, api_url, artifact_id, version)
    if entry is None:
        raise SystemExit(f"No version {version} for {spec.artifact_type} {spec.name}")
    version_id = int(entry["id"])
    if entry.get("is_published"):
        print(f"[ok] already published {spec.artifact_type} {spec.name}@{version}")
        return

    if dry_run:
        print(f"[dry-run] would publish version {version} for {spec.artifact_type} {spec.name}")
        return

    max_attempts = 30
    for attempt in range(max_attempts):
        entry = version_entry(session, api_url, artifact_id, version) or entry
        if entry.get("is_published"):
            print(f"[ok] already published {spec.artifact_type} {spec.name}@{version}")
            return

        scan_status = str(entry.get("verification_status") or "").upper()
        if scan_status in {"", "PENDING"}:
            wait_s = 15
            print(
                f"[wait] scan pending for {spec.name}; checking again in {wait_s}s "
                f"(attempt {attempt + 1}/{max_attempts})"
            )
            time.sleep(wait_s)
            continue

        if scan_status == "ERROR":
            if approve_artifact_version(session, api_url, artifact_id, version_id, spec.name):
                scan_status = "APPROVED_BY_HUMAN"
            else:
                raise SystemExit(
                    f"Cannot publish {spec.artifact_type} {spec.name}@{version}: "
                    f"verification_status=ERROR"
                )

        if scan_status == "REJECTED":
            raise SystemExit(
                f"Cannot publish {spec.artifact_type} {spec.name}@{version}: "
                f"verification_status=REJECTED"
            )

        if scan_status == "WARNING":
            if approve_artifact_version(session, api_url, artifact_id, version_id, spec.name):
                scan_status = "APPROVED_BY_HUMAN"
            else:
                time.sleep(15)
                continue

        if scan_status not in {"CLEAN", "APPROVED_BY_HUMAN"}:
            wait_s = 15
            print(
                f"[wait] {spec.name} status={scan_status}; retrying in {wait_s}s "
                f"(attempt {attempt + 1}/{max_attempts})"
            )
            time.sleep(wait_s)
            continue

        response = session.post(
            f"{api_url}/api/skills/{artifact_id}/versions/{version_id}/publish",
            timeout=120,
        )
        if response.status_code in (200, 201):
            payload = response.json()
            if payload.get("published"):
                print(f"[ok] published {spec.artifact_type} {spec.name}@{version}")
                return
            print(
                f"[warn] publish returned {response.status_code} for {spec.name}: "
                f"{response.text[:300]}"
            )
            return

        body: dict = {}
        try:
            body = response.json()
        except ValueError:
            body = {}

        if response.status_code in (409, 429):
            body_status = str(body.get("status") or "").upper()
            if body_status == "WARNING":
                approve_artifact_version(session, api_url, artifact_id, version_id, spec.name)
                continue
            retry_after = min(int(body.get("retry_after_s", 30)), 60)
            reason = body_status or body.get("message") or response.text[:120]
            print(
                f"[wait] {spec.name} not ready ({reason}); retrying in {retry_after}s "
                f"(attempt {attempt + 1}/{max_attempts})"
            )
            time.sleep(retry_after)
            continue

        raise SystemExit(
            f"POST /api/skills/{artifact_id}/versions/{version_id}/publish failed: "
            f"{response.status_code} {response.text}"
        )

    raise SystemExit(
        f"Timed out publishing stable version for {spec.artifact_type} {spec.name}@{version}"
    )


def promote_external_profile_items(
    session: requests.Session,
    api_url: str,
    items: list[dict[str, object]],
    *,
    dry_run: bool,
) -> None:
    """Ensure third-party profile items have a published stable version on this portal."""
    for item in items:
        name = str(item["artifact_name"])
        artifact_type = str(item["artifact_type"])
        if dry_run:
            print(f"[dry-run] would promote external {artifact_type} {name}")
            continue

        artifact_id = try_resolve_artifact_id(session, api_url, name, artifact_type)
        if artifact_id is None:
            print(f"[skip] external {artifact_type} {name} not found on portal")
            continue

        response = session.get(
            f"{api_url}/api/skills",
            params={"q": name, "context": "admin"},
            timeout=120,
        )
        list_item = next(
            (
                entry
                for entry in response.json().get("items", [])
                if entry.get("name") == name and entry.get("artifact_type") == artifact_type
            ),
            None,
        )
        target_version = (
            str(list_item.get("current_version") or "").strip()
            if list_item is not None
            else ""
        )
        if not target_version:
            print(f"[skip] external {name} has no current_version")
            continue

        spec = ArtifactSpec(
            name=name,
            artifact_type=artifact_type,
            source_path=".",
            description="external profile item",
            publish=True,
            include_in_profile=False,
        )
        publish_artifact_version(session, api_url, spec, target_version, dry_run=False)


def artifact_exists(session: requests.Session, api_url: str, name: str, artifact_type: str) -> bool:
    response = api_request(
        session,
        "GET",
        f"{api_url}/api/skills",
        params={"q": name, "context": "admin"},
    )
    items = response.json().get("items", [])
    return any(item.get("name") == name and item.get("artifact_type") == artifact_type for item in items)


def ensure_profile(
    session: requests.Session,
    api_url: str,
    team_id: int,
    owner_user_id_2: str,
    dry_run: bool,
) -> int:
    response = session.get(
        f"{api_url}/api/profiles/by-slug/wise-feature-lifecycle",
        params={"tool": "admin", "context": "admin"},
        timeout=120,
    )
    if response.status_code == 200:
        profile = response.json()["profile"]
        profile_id = int(profile["id"])
        current_team_id = profile.get("team_id")
        current_visibility = (profile.get("visibility") or "").strip().lower()
    elif response.status_code == 404:
        payload = {
            "slug": "wise-feature-lifecycle",
            "name": "WISE Feature Lifecycle",
            "description": "Git-first feature lifecycle profile for Skills Portal teams.",
            "persona": "developer",
            "tags": ["wise", "lifecycle", "governance", "security"],
            "visibility": "private",
            "is_official": False,
            "source_repo": "essensys-hub/essensys-feature-lifecycle",
            "owner_user_id_2": owner_user_id_2,
        }
        if dry_run:
            print(f"[dry-run] would create profile: {json.dumps(payload)}")
            return 0
        created = api_request(
            session,
            "POST",
            f"{api_url}/api/profiles",
            expected=(200, 201),
            json=payload,
        ).json()["profile"]
        profile_id = int(created["id"])
        current_team_id = created.get("team_id")
        current_visibility = (created.get("visibility") or "").strip().lower()
    else:
        raise SystemExit(f"Failed to fetch profile slug: {response.status_code} {response.text}")

    if current_visibility == "team" and current_team_id == team_id:
        print(f"[ok] profile {profile_id} already bound to team_id={team_id}, skipping PATCH.")
        return profile_id

    patch_payload = {
        "name": "WISE Feature Lifecycle",
        "description": "Git-first feature lifecycle profile for Skills Portal teams.",
        "persona": "developer",
        "tags": ["wise", "lifecycle", "governance", "security"],
        "visibility": "team",
        "team_id": team_id,
    }
    if dry_run:
        print(f"[dry-run] would patch profile {profile_id}: {json.dumps(patch_payload)}")
        return profile_id

    patch_response = session.patch(
        f"{api_url}/api/profiles/{profile_id}",
        json=patch_payload,
        timeout=120,
    )
    if patch_response.status_code in (200, 201):
        print(f"[ok] profile {profile_id} bound to team_id={team_id}.")
    elif patch_response.status_code == 403:
        print(
            f"[warn] PATCH /api/profiles/{profile_id} returned 403. "
            f"The API key user is not a member of team_id={team_id}. "
            f"Open the Skills Portal admin UI as {owner_user_id_2}, edit profile {profile_id}, "
            f"and set visibility=team, team_id={team_id}. "
            f"Artifacts and the profile version still publish from this run."
        )
    else:
        raise SystemExit(
            f"PATCH /api/profiles/{profile_id} failed: {patch_response.status_code} {patch_response.text}"
        )
    return profile_id


def find_existing_version(
    session: requests.Session,
    api_url: str,
    profile_id: int,
    version: str,
) -> dict | None:
    response = api_request(
        session,
        "GET",
        f"{api_url}/api/profiles/{profile_id}?tool=admin&context=admin",
        expected=(200,),
    )
    payload = response.json()
    for entry in payload.get("versions", []) or []:
        if str(entry.get("version")) == version:
            return entry
    return None


def create_profile_version(session: requests.Session, api_url: str, profile_id: int, version: str, dry_run: bool) -> tuple[int, str]:
    items: list[dict[str, object]] = []
    order = 1
    for spec in LOCAL_ARTIFACTS:
        if not spec.include_in_profile:
            continue
        items.append(
            {
                "artifact_type": spec.artifact_type,
                "artifact_name": spec.name,
                "version_selector": "latest",
                "tool_scope": "cursor",
                "order": order,
            }
        )
        order += 1
    for extra in EXTERNAL_PROFILE_ITEMS + OPTIONAL_PROFILE_ITEMS:
        item = dict(extra)
        item["order"] = order
        items.append(item)
        order += 1

    payload = {
        "version": version,
        "changelog": "Initial lifecycle profile for team-scoped rollout.",
        "items": items,
    }
    if dry_run:
        print(f"[dry-run] would create profile version: {json.dumps(payload)}")
        return 0, "draft"

    existing = find_existing_version(session, api_url, profile_id, version)
    if existing is not None:
        existing_id = int(existing["id"])
        existing_status = str(existing.get("status") or "draft")
        print(
            json.dumps(
                {
                    "event": "version_already_present",
                    "profile_id": profile_id,
                    "version_id": existing_id,
                    "version": version,
                    "status": existing_status,
                }
            )
        )
        return existing_id, existing_status

    version_response = api_request(
        session,
        "POST",
        f"{api_url}/api/profiles/{profile_id}/versions",
        expected=(200, 201),
        json=payload,
    ).json()["version"]
    return int(version_response["id"]), str(version_response.get("status") or "draft")


def main() -> int:
    args = build_parser().parse_args()
    session = requests.Session()
    session.headers.update({
        "X-API-Key": args.api_key,
        "Content-Type": "application/json",
    })

    published_names: list[str] = []
    for spec in LOCAL_ARTIFACTS:
        if not spec.publish:
            continue
        payload = load_artifact(spec)
        payload["version"] = args.version
        if args.dry_run:
            print(f"[dry-run] would publish {spec.artifact_type} {spec.name}")
        else:
            artifact_id = try_resolve_artifact_id(
                session, args.api_url, spec.name, spec.artifact_type
            )
            existing_version = (
                version_entry(session, args.api_url, artifact_id, args.version)
                if artifact_id is not None
                else None
            )
            if existing_version is None or version_needs_reupload(existing_version):
                api_request(
                    session,
                    "POST",
                    f"{args.api_url}/api/official/publish",
                    expected=(200, 201),
                    json=payload,
                )
                if existing_version is not None:
                    print(
                        f"[retry] re-uploaded {spec.artifact_type} {spec.name}@{args.version} "
                        f"after verification_status="
                        f"{existing_version.get('verification_status')}"
                    )
            else:
                print(
                    f"[skip] upload {spec.artifact_type} {spec.name}@{args.version} "
                    "already present"
                )
            publish_artifact_version(
                session,
                args.api_url,
                spec,
                args.version,
                dry_run=False,
            )
        published_names.append(spec.name)

    # Drop optional MCPs that are still absent on the target portal.
    available_optional_items = [
        item
        for item in OPTIONAL_PROFILE_ITEMS
        if artifact_exists(session, args.api_url, item["artifact_name"], item["artifact_type"])
    ]
    OPTIONAL_PROFILE_ITEMS.clear()
    OPTIONAL_PROFILE_ITEMS.extend(available_optional_items)

    profile_id = ensure_profile(
        session,
        args.api_url,
        args.team_id,
        args.owner_user_id_2,
        args.dry_run,
    )
    version_id, version_status = create_profile_version(
        session, args.api_url, profile_id, args.version, args.dry_run
    )

    if args.dry_run:
        print(f"[dry-run] would publish profile wise-feature-lifecycle version {args.version}")
        return 0

    promote_external_profile_items(
        session,
        args.api_url,
        EXTERNAL_PROFILE_ITEMS,
        dry_run=False,
    )

    if version_status == "published":
        print(json.dumps({
            "event": "version_already_published",
            "profile_id": profile_id,
            "version_id": version_id,
            "version": args.version,
        }))
    else:
        api_request(
            session,
            "POST",
            f"{args.api_url}/api/profiles/{profile_id}/versions/{version_id}/publish",
            expected=(200, 201),
        )
    print(json.dumps({
        "published_artifacts": published_names,
        "profile_id": profile_id,
        "profile_version_id": version_id,
        "profile_slug": "wise-feature-lifecycle",
        "optional_profile_items": [item["artifact_name"] for item in available_optional_items],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
