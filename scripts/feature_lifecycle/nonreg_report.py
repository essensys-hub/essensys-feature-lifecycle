#!/usr/bin/env python3
"""Normalise JUnit XML and Playwright JSON results into a single report per NR-* non-regression test."""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from project_sync import is_flaky  # noqa: E402


NR_ID_PATTERN = re.compile(r"NR-[a-z0-9-]+-\d+")
# Identifiants dans des noms de tests où « - » est interdit (Go, Kotlin/JUnit) : NR_android_3 → NR-android-3.
NR_UNDERSCORE_PATTERN = re.compile(r"(?<![A-Za-z0-9])NR_([a-z0-9_]+?)_(\d+)(?![0-9])")
SOURCE_SUFFIXES = {".kt", ".java", ".go", ".py", ".ts", ".tsx", ".js", ".swift"}
ISSUE_PATTERN = re.compile(r"(?:[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)?#\d+")
ISSUE_URL_PATTERN = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/(?:issues|pull)/(\d+)")
NR_TAG_PATTERN = re.compile(r"(?<![A-Za-z0-9])@nr\b", re.IGNORECASE)
NR_PROPERTY_NAMES = {"nr", "nr_id", "nr-id"}
ISSUE_PROPERTY_NAMES = {"issue", "nr_issue", "nr-issue"}
HISTORY_LIMIT = 10
STATUS_ORDER = {"failed": 0, "passed": 1, "skipped": 2}
PLAYWRIGHT_FAILED = {"failed", "timedOut", "interrupted"}


@dataclass
class Case:
    """One raw test execution carrying an NR id (or an @nr tag)."""

    nr_id: str | None
    name: str
    source: str
    status: str
    issue: str | None
    retried_pass: bool = False


@dataclass
class ParseOutcome:
    cases: list[Case] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the consolidated non-regression report (JSON + markdown) from test outputs."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="JUnit XML / Playwright JSON files, directories (searched recursively) or glob patterns.",
    )
    parser.add_argument("--history", help="Previous report JSON, used to extend per-test history.")
    parser.add_argument(
        "--sources",
        nargs="*",
        default=[],
        help="Source directories scanned for `NR: NR-<repo>-<n> <issue>` comments (issue lookup for JUnit names).",
    )
    parser.add_argument("--out", required=True, help="Output JSON report path.")
    parser.add_argument("--markdown", required=True, help="Output markdown report path.")
    parser.add_argument("--json", action="store_true", help="Also print the JSON report on stdout.")
    return parser


# --------------------------------------------------------------------------- extraction helpers


def normalize_issue(raw: str | None) -> str | None:
    if not raw:
        return None
    url = ISSUE_URL_PATTERN.search(raw)
    if url:
        return f"{url.group(1)}/{url.group(2)}#{url.group(3)}"
    match = ISSUE_PATTERN.search(raw)
    return match.group(0) if match else None


def nr_from_text(text: str | None) -> tuple[str | None, str | None]:
    """Find an NR id in text and the issue reference on the same line (after the id)."""
    if not text:
        return None, None
    for line in text.splitlines():
        match = NR_ID_PATTERN.search(line)
        if match:
            return match.group(0), normalize_issue(line[match.end():])
        underscored = NR_UNDERSCORE_PATTERN.search(line)
        if underscored:
            nr_id = f"NR-{underscored.group(1).replace('_', '-')}-{underscored.group(2)}"
            return nr_id, None
    return None, None


def scan_sources(directories: list[str]) -> dict[str, str]:
    """Map NR id → issue from `NR: NR-<repo>-<n> <issue>` comments found in source files."""
    issues: dict[str, str] = {}
    for directory in directories:
        root = Path(directory)
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix not in SOURCE_SUFFIXES or not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for line in text.splitlines():
                if not re.search(r"NR\s*:", line):
                    continue
                nr_id, issue = nr_from_text(line)
                if nr_id and issue:
                    issues.setdefault(nr_id, issue)
    return issues


def merge(found: tuple[str | None, str | None], nr_id: str | None, issue: str | None) -> tuple[str | None, str | None]:
    return nr_id or found[0], issue or (found[1] if (nr_id is None or found[0] == nr_id) else None)


# --------------------------------------------------------------------------- JUnit


def junit_status(case: ET.Element) -> str:
    if case.find("failure") is not None or case.find("error") is not None:
        return "failed"
    if case.find("skipped") is not None:
        return "skipped"
    return "passed"


def parse_junit(path: Path) -> ParseOutcome:
    outcome = ParseOutcome()
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        outcome.errors.append(f"{path}: unreadable JUnit XML ({exc})")
        return outcome
    for case in root.iter("testcase"):
        name = case.get("name", "")
        classname = case.get("classname", "")
        nr_id: str | None = None
        issue: str | None = None
        for prop in case.iter("property"):
            key = (prop.get("name") or "").lower()
            value = prop.get("value") if prop.get("value") is not None else (prop.text or "")
            if key in NR_PROPERTY_NAMES:
                found = nr_from_text(value)
                nr_id = nr_id or found[0]
                issue = issue or found[1]
            elif key in ISSUE_PROPERTY_NAMES:
                issue = issue or normalize_issue(value)
        for text in (name, classname):
            nr_id, issue = merge(nr_from_text(text), nr_id, issue)
        outputs = [el.text or "" for tag in ("system-out", "system-err") for el in case.findall(tag)]
        outputs += [(el.text or "") + "\n" + (el.get("message") or "") for tag in ("failure", "error")
                    for el in case.findall(tag)]
        for text in outputs:
            for line in text.splitlines():
                if re.search(r"(?://|#)?\s*NR\s*:", line) or NR_ID_PATTERN.search(line):
                    nr_id, issue = merge(nr_from_text(line), nr_id, issue)
        tagged = bool(NR_TAG_PATTERN.search(name) or NR_TAG_PATTERN.search(classname))
        if nr_id is None and not tagged:
            continue
        display = f"{classname}.{name}" if classname and not name.startswith(classname) else name
        outcome.cases.append(Case(nr_id, display, str(path), junit_status(case), issue))
    return outcome


# --------------------------------------------------------------------------- Playwright


def _iter_specs(suites: Iterable[dict[str, Any]], titles: list[str]):
    for suite in suites or []:
        path = titles + ([suite["title"]] if suite.get("title") else [])
        for spec in suite.get("specs") or []:
            yield path, spec
        yield from _iter_specs(suite.get("suites") or [], path)


def playwright_status(test: dict[str, Any]) -> tuple[str, bool]:
    results = test.get("results") or []
    overall = test.get("status")
    if overall == "skipped" or (results and all(r.get("status") == "skipped" for r in results)):
        return "skipped", False
    if results:
        last = results[-1].get("status")
        if last in PLAYWRIGHT_FAILED:
            return "failed", False
        if last == "passed":
            retried = overall == "flaky" or any(r.get("status") in PLAYWRIGHT_FAILED for r in results[:-1])
            return "passed", retried
    if overall == "unexpected":
        return "failed", False
    if overall in ("expected", "flaky"):
        return "passed", overall == "flaky"
    return "skipped", False


def parse_playwright(path: Path) -> ParseOutcome:
    outcome = ParseOutcome()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        outcome.errors.append(f"{path}: unreadable Playwright JSON ({exc})")
        return outcome
    for titles, spec in _iter_specs(data.get("suites") or [], []):
        title = spec.get("title", "")
        tags = [str(tag) for tag in spec.get("tags") or []]
        for test in spec.get("tests") or [{}]:
            annotations = list(test.get("annotations") or [])
            for result in test.get("results") or []:
                annotations += result.get("annotations") or []
            nr_id, issue = None, None
            for annotation in annotations:
                kind = (annotation.get("type") or "").lower()
                desc = annotation.get("description") or ""
                if kind in ("nr", "nr-id", "nr_id"):
                    nr_id, issue = merge(nr_from_text(desc), nr_id, issue)
                elif kind == "issue":
                    issue = issue or normalize_issue(desc)
            for tag in tags:
                found = NR_ID_PATTERN.search(tag)
                if found:
                    nr_id = nr_id or found.group(0)
            nr_id, issue = merge(nr_from_text(title), nr_id, issue)
            tagged = any(tag.lower() == "@nr" for tag in tags) or bool(NR_TAG_PATTERN.search(title))
            if nr_id is None and not tagged:
                continue
            project = test.get("projectName")
            name = " › ".join(titles + [title]) + (f" [{project}]" if project else "")
            status, retried = playwright_status(test)
            source = spec.get("file") or str(path)
            outcome.cases.append(Case(nr_id, name, source, status, issue, retried))
    return outcome


# --------------------------------------------------------------------------- aggregation


def expand_inputs(raw_inputs: list[str]) -> tuple[list[Path], list[str]]:
    paths: list[Path] = []
    errors: list[str] = []
    for raw in raw_inputs:
        candidate = Path(raw)
        if candidate.is_dir():
            paths += sorted(p for p in candidate.rglob("*") if p.suffix in (".xml", ".json") and p.is_file())
        elif candidate.is_file():
            paths.append(candidate)
        else:
            matches = sorted(Path(p) for p in glob.glob(raw, recursive=True) if Path(p).is_file())
            if matches:
                paths += matches
            else:
                errors.append(f"{raw}: no such input")
    return paths, errors


def parse_input(path: Path) -> ParseOutcome:
    if path.suffix == ".json":
        return parse_playwright(path)
    return parse_junit(path)


def load_history(path: str | None) -> dict[str, list[str]]:
    if not path or not Path(path).exists():
        return {}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {t["id"]: list(t.get("history") or []) for t in data.get("tests") or [] if t.get("id")}


def build_report(
    outcomes: list[ParseOutcome],
    previous: dict[str, list[str]] | None = None,
    generated_at: str | None = None,
    source_issues: dict[str, str] | None = None,
) -> dict[str, Any]:
    previous = previous or {}
    source_issues = source_issues or {}
    errors: list[str] = []
    grouped: dict[str, list[Case]] = {}
    for outcome in outcomes:
        errors += outcome.errors
        for case in outcome.cases:
            if case.nr_id is None:
                errors.append(f"{case.source}: `{case.name}` is tagged @nr without an `NR-<repo>-<n>` identifier")
                continue
            grouped.setdefault(case.nr_id, []).append(case)

    tests: list[dict[str, Any]] = []
    for nr_id in sorted(grouped):
        cases = grouped[nr_id]
        status = min((c.status for c in cases), key=lambda s: STATUS_ORDER[s])
        issue = next((c.issue for c in cases if c.issue), None) or source_issues.get(nr_id)
        if issue is None:
            errors.append(f"{nr_id} ({cases[0].name}): missing issue reference (`#<n>` or `owner/repo#<n>`)")
        history = (previous.get(nr_id, []) + [status])[-HISTORY_LIMIT:]
        sources = sorted({c.source for c in cases})
        tests.append(
            {
                "id": nr_id,
                "name": cases[0].name,
                "source": ", ".join(sources),
                "status": status,
                "issue": issue,
                "cases": len(cases),
                "flaky": is_flaky(history) or any(c.retried_pass for c in cases),
                "history": history,
            }
        )

    totals = {
        "passed": sum(1 for t in tests if t["status"] == "passed"),
        "failed": sum(1 for t in tests if t["status"] == "failed"),
        "skipped": sum(1 for t in tests if t["status"] == "skipped"),
        "flaky": sum(1 for t in tests if t["flaky"]),
    }
    return {
        "generated_at": generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "totals": totals,
        "tests": tests,
        "errors": errors,
    }


def emit_markdown(report: dict[str, Any]) -> str:
    totals = report["totals"]
    lines = [
        "# Non-Regression Report",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Passed: `{totals['passed']}` · Failed: `{totals['failed']}` · "
        f"Skipped: `{totals['skipped']}` · Flaky: `{totals['flaky']}`",
        "",
    ]
    if report["tests"]:
        lines += ["| NR | Status | Issue | Test | History |", "| --- | --- | --- | --- | --- |"]
        for test in report["tests"]:
            status = test["status"].upper() + (" (flaky)" if test["flaky"] else "")
            name = test["name"].replace("|", "\\|")
            lines.append(
                f"| `{test['id']}` | {status} | {test['issue'] or '—'} | {name} | {' → '.join(test['history'])} |"
            )
    else:
        lines.append("- No NR-* test found in the inputs.")
    if report["errors"]:
        lines += ["", "## Errors", ""] + [f"- Error: {error}" for error in report["errors"]]
    return "\n".join(lines)


def write_github_step_summary(markdown: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write(markdown + "\n")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths, input_errors = expand_inputs(args.inputs)
    outcomes = [ParseOutcome(errors=input_errors)] + [parse_input(path) for path in paths]
    report = build_report(outcomes, load_history(args.history), source_issues=scan_sources(args.sources))
    markdown = emit_markdown(report)
    Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(args.markdown).write_text(markdown + "\n", encoding="utf-8")
    write_github_step_summary(markdown)
    print(json.dumps(report, indent=2, ensure_ascii=False) if args.json else markdown)
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
