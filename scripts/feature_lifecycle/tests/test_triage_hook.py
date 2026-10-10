from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HOOK = REPO / "claude" / "hooks" / "block_self_validation.py"
sys.path.insert(0, str(HOOK.parent))

import block_self_validation as hook  # noqa: E402


def run_hook(payload: dict) -> int:
    proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True)
    return proc.returncode


class HookTest(unittest.TestCase):
    # NR: NR-lifecycle-5 essensys-hub/essensys-feature-lifecycle#18
    def test_hook_blocks_gh_add_label_valide_NR_lifecycle_5(self):
        for cmd in ("gh issue edit 5 --add-label valide",
                    "gh issue edit 5 -R essensys-hub/essensys-support --add-label bug,valide",
                    'gh issue edit 5 --add-label "valide"',
                    "gh pr edit 3 --add-label=valide",
                    "gh api repos/essensys-hub/essensys-support/issues/5/labels -f 'labels[]=valide'"):
            self.assertEqual(run_hook({"tool_name": "Bash", "tool_input": {"command": cmd}}), 2, cmd)

    def test_hook_allows_other_labels_and_reads(self):
        for cmd in ("gh issue edit 5 --add-label a-valider",
                    "gh issue edit 5 --add-label besoin-info --remove-label valide",
                    "gh issue list --label valide",
                    "gh issue view 5 --json labels",
                    "python3 triage_gate.py essensys-hub/essensys-support#5"):
            self.assertEqual(run_hook({"tool_name": "Bash", "tool_input": {"command": cmd}}), 0, cmd)

    def test_hook_blocks_mcp_label_write(self):
        self.assertTrue(hook.should_block({"tool_name": "mcp__github__issue_write",
                                           "tool_input": {"method": "update", "labels": ["bug", "valide"]}}))
        self.assertFalse(hook.should_block({"tool_name": "mcp__github__issue_write",
                                            "tool_input": {"method": "update", "labels": ["a-valider"]}}))
        self.assertFalse(hook.should_block({"tool_name": "mcp__github__issue_read",
                                            "tool_input": {"labels": ["valide"]}}))

    def test_invalid_payload_does_not_block(self):
        proc = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)


class InstallTest(unittest.TestCase):
    def test_install_merges_hook_once_and_keeps_settings(self):
        with tempfile.TemporaryDirectory() as ws:
            settings = Path(ws) / ".claude" / "settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text(json.dumps({"permissions": {"defaultMode": "plan"}}), encoding="utf-8")
            for _ in range(2):
                subprocess.run(["bash", str(REPO / "scripts" / "install-claude.sh"), ws], check=True,
                               capture_output=True, text=True, env={**os.environ})
            data = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(data["permissions"], {"defaultMode": "plan"})
            entries = [h for e in data["hooks"]["PreToolUse"] for h in e["hooks"]]
            self.assertEqual(len([h for h in entries if "block_self_validation" in h["command"]]), 1)
            self.assertTrue((Path(ws) / ".claude" / "hooks" / "block_self_validation.py").exists())


if __name__ == "__main__":
    unittest.main()
