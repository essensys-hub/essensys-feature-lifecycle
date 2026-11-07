from __future__ import annotations

import unittest

from scripts.feature_lifecycle.tests._helpers import FIXTURES  # noqa: F401  (ajoute le dossier des scripts au path)

import check_feature_gate as gate

ISSUE = "essensys-hub/essensys-feature-lifecycle#43"


def matrix(**over):
    base = {b: {"scope": "not-concerned", "reason": "hors périmètre"} for b in gate.BRICKS}
    base.update(over)
    return base


def run(manifest):
    result = gate.ManifestResult(path="m.json", errors=[], warnings=[])
    gate.check_bricks(manifest, result)
    return result


class BrickMatrixTest(unittest.TestCase):
    def test_old_feature_without_matrix_is_valid(self) -> None:
        r = run({"status": "archived"})
        self.assertEqual((r.errors, r.warnings), ([], []))

    def test_new_feature_without_matrix_warns(self) -> None:
        r = run({"status": "in-progress"})
        self.assertEqual(r.errors, [])
        self.assertEqual(len(r.warnings), 1)

    def test_missing_brick_is_an_error(self) -> None:
        m = matrix()
        del m["android"]
        r = run({"status": "in-progress", "bricks": m})
        self.assertTrue(any("android" in e for e in r.errors))

    def test_not_concerned_requires_reason(self) -> None:
        r = run({"status": "in-progress", "bricks": matrix(iphone={"scope": "not-concerned"})})
        self.assertTrue(any("sans raison" in e for e in r.errors))

    def test_concerned_requires_issue(self) -> None:
        r = run({"status": "in-progress", "bricks": matrix(cloud={"scope": "concerned"})})
        self.assertTrue(any("sans sub-issue" in e for e in r.errors))

    def test_undelivered_brick_blocks_merged(self) -> None:
        b = matrix(cloud={"scope": "concerned", "issue": ISSUE})
        self.assertEqual(run({"status": "in-progress", "bricks": b}).errors, [])
        self.assertTrue(run({"status": "merged", "bricks": b}).errors)

    def test_all_delivered_passes(self) -> None:
        b = matrix(cloud={"scope": "concerned", "issue": ISSUE, "delivered": True})
        self.assertEqual(run({"status": "merged", "bricks": b}).errors, [])


if __name__ == "__main__":
    unittest.main()
