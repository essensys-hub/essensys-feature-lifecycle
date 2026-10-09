#!/usr/bin/env python3
"""Check that a pull request is linked to a feature, an issue and (for bug fixes) a non-regression test."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from project_sync import parse_pr_body  # noqa: E402


EXEMPT_AUTHORS = {"dependabot[bot]"}
EXEMPT_LABEL = "chore/no-feature"
NR_EXEMPT_LABEL = "nr-exempt"
EXPECTED_FORMAT = (
    "```\n"
    "Feature: <feature-id>\n"
    "Closes #<issue>   (ou Fixes/Resolves #<issue>, ou Refs #<issue>)\n"
    "```"
)


@dataclass
class LinkageResult:
    mode: str
    exempt: bool = False
    feature_id: str | None = None
    closes: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check PR linkage: Feature line, issue reference, non-regression test for closed Bugs."
    )
    parser.add_argument("--pr-body-file", required=True, help="File containing the PR body.")
    parser.add_argument("--pr-author", default="", help="PR author login (dependabot[bot] is exempt).")
    parser.add_argument("--labels", default="", help="Comma-separated PR labels.")
    parser.add_argument("--changed-files-file", help="File listing changed paths, one per line.")
    parser.add_argument(
        "--closes-bug-numbers",
        default="",
        help="Comma-separated numbers of Bug issues closed by the PR (resolved by the workflow).",
    )
    parser.add_argument("--repo-root", default=os.getcwd(), help="Repository checkout root (default: cwd).")
    parser.add_argument(
        "--features-dir",
        help="Optional features/ directory; when given, `Feature: <id>` must match <dir>/<id>.json.",
    )
    parser.add_argument(
        "--mode",
        choices=("warn", "block"),
        default=os.environ.get("FEATURE_GATE_MODE", "warn"),
        help="warn: always exit 0; block: exit 1 on errors (default: $FEATURE_GATE_MODE or warn).",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    return parser


def split_csv(raw: str | None) -> list[str]:
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def read_lines(path: str | None) -> list[str]:
    if not path:
        return []
    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def bug_reference_pattern(number: int) -> re.Pattern[str]:
    return re.compile(rf"(?<![0-9A-Za-z])#{number}(?!\d)")


def file_references_bug(path: Path, number: int) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    pattern = bug_reference_pattern(number)
    return any("NR-" in line and pattern.search(line) for line in content.splitlines())


def check_linkage(
    body: str,
    *,
    author: str = "",
    labels: list[str] | None = None,
    changed_files: list[str] | None = None,
    closes_bugs: list[int] | None = None,
    repo_root: Path | None = None,
    features_dir: Path | None = None,
    mode: str = "warn",
) -> LinkageResult:
    labels = labels or []
    result = LinkageResult(mode=mode)
    if author in EXEMPT_AUTHORS or EXEMPT_LABEL in labels:
        result.exempt = True
        return result

    links = parse_pr_body(body)
    result.feature_id, result.closes, result.refs = links.feature_id, links.closes, links.refs

    if not links.feature_id:
        result.errors.append("Missing `Feature: <id>` line in the PR body.")
    elif features_dir is not None and not (features_dir / f"{links.feature_id}.json").exists():
        result.errors.append(f"No manifest found for feature `{links.feature_id}` in `{features_dir}`.")

    if not links.closes and not links.refs:
        result.errors.append("Missing issue reference (`Closes|Fixes|Resolves #<n>` or `Refs #<n>`).")

    root = repo_root or Path.cwd()
    files = [root / item for item in (changed_files or [])]
    for number in closes_bugs or []:
        if NR_EXEMPT_LABEL in labels:
            result.warnings.append(f"Bug #{number}: non-regression test waived by label `{NR_EXEMPT_LABEL}`.")
            continue
        if not any(file_references_bug(path, number) for path in files):
            result.errors.append(
                f"PR closes Bug #{number} but no changed file holds a non-regression test "
                f"referencing it (expected a line with `NR-<repo>-<n>` and `#{number}`, "
                f"or the `{NR_EXEMPT_LABEL}` label with a justification)."
            )
    return result


def emit_markdown(result: LinkageResult) -> str:
    status = "OK" if result.ok else ("FAIL" if result.mode == "block" else "WARN")
    lines = ["# PR Linkage Check", "", f"- Status: `{status}`", f"- Mode: `{result.mode}`"]
    if result.exempt:
        lines.append("- Exempt PR (Dependabot or `chore/no-feature`).")
        return "\n".join(lines)
    lines.append(f"- Feature: `{result.feature_id or '∅'}`")
    lines.append(f"- Closes: {', '.join(f'`{r}`' for r in result.closes) or '∅'}")
    lines.append(f"- Refs: {', '.join(f'`{r}`' for r in result.refs) or '∅'}")
    lines.append("")
    for error in result.errors:
        lines.append(f"- Error: {error}")
    for warning in result.warnings:
        lines.append(f"- Warning: {warning}")
    if result.errors:
        lines += ["", "Format attendu dans la description de la PR :", "", EXPECTED_FORMAT]
    return "\n".join(lines)


def write_github_step_summary(markdown: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write(markdown + "\n")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    body = Path(args.pr_body_file).read_text(encoding="utf-8")
    try:
        bugs = [int(item.lstrip("#")) for item in split_csv(args.closes_bug_numbers)]
    except ValueError:
        print(f"Invalid --closes-bug-numbers: {args.closes_bug_numbers}", file=sys.stderr)
        return 2
    result = check_linkage(
        body,
        author=args.pr_author,
        labels=split_csv(args.labels),
        changed_files=read_lines(args.changed_files_file),
        closes_bugs=bugs,
        repo_root=Path(args.repo_root),
        features_dir=Path(args.features_dir) if args.features_dir else None,
        mode=args.mode,
    )
    markdown = emit_markdown(result)
    write_github_step_summary(markdown)
    if args.json:
        payload = {
            "ok": result.ok,
            "mode": result.mode,
            "exempt": result.exempt,
            "feature_id": result.feature_id,
            "closes": result.closes,
            "refs": result.refs,
            "errors": result.errors,
            "warnings": result.warnings,
            "markdown": markdown,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(markdown)
    return 1 if result.errors and result.mode == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
