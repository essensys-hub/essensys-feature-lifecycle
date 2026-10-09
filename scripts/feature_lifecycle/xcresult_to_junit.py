#!/usr/bin/env python3
"""Convert an Xcode .xcresult bundle (xcresulttool test-results) into JUnit XML for nonreg_report.py."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


STATUS = {"Passed": "passed", "Failed": "failed", "Skipped": "skipped", "Expected Failure": "passed"}


def load_tests(xcresult: Path, runner=subprocess.run) -> dict[str, Any]:
    completed = runner(
        ["xcrun", "xcresulttool", "get", "test-results", "tests", "--path", str(xcresult)],
        capture_output=True, text=True, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "xcresulttool failed")
    return json.loads(completed.stdout)


def iter_cases(node: dict[str, Any], suite: str | None = None):
    kind = node.get("nodeType")
    if kind == "Test Case":
        yield suite or "", node
        return
    next_suite = node.get("name") if kind == "Test Suite" else suite
    for child in node.get("children", []) or []:
        yield from iter_cases(child, next_suite)


def failure_message(case: dict[str, Any]) -> str:
    messages = [c.get("name", "") for c in case.get("children", []) or [] if c.get("nodeType") == "Failure Message"]
    return "\n".join(messages) or "failed"


def to_junit(data: dict[str, Any]) -> ET.Element:
    root = ET.Element("testsuites")
    suites: dict[str, ET.Element] = {}
    for plan in data.get("testNodes", []):
        for suite, case in iter_cases(plan):
            element = suites.get(suite)
            if element is None:
                element = suites[suite] = ET.SubElement(root, "testsuite", name=suite)
            name = (case.get("name") or "").removesuffix("()")
            testcase = ET.SubElement(element, "testcase", classname=suite, name=name)
            status = STATUS.get(case.get("result", ""), "failed")
            if status == "failed":
                ET.SubElement(testcase, "failure", message=failure_message(case))
            elif status == "skipped":
                ET.SubElement(testcase, "skipped")
    for element in suites.values():
        cases = element.findall("testcase")
        element.set("tests", str(len(cases)))
        element.set("failures", str(sum(1 for c in cases if c.find("failure") is not None)))
        element.set("skipped", str(sum(1 for c in cases if c.find("skipped") is not None)))
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xcresult", type=Path)
    parser.add_argument("--out", required=True, type=Path, help="JUnit XML output path")
    args = parser.parse_args(argv)
    try:
        root = to_junit(load_tests(args.xcresult))
    except (RuntimeError, json.JSONDecodeError) as exc:
        print(f"xcresult_to_junit: {exc}", file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(args.out, encoding="utf-8", xml_declaration=True)
    total = sum(int(s.get("tests", "0")) for s in root)
    print(f"{args.out}: {total} test(s) in {len(root)} suite(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
