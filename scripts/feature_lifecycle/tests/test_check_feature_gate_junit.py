from __future__ import annotations

import unittest

from scripts.feature_lifecycle.tests._helpers import FIXTURES  # noqa: F401  (ajoute le dossier des scripts au path)

import check_feature_gate as gate


KOTLIN = """
class AuthRepositoryTest {
    // NR: NR-android-2 essensys-hub/essensys-android-phone-apps#2
    @Test
    fun unauthorized_response_clears_session_and_shows_login_NR_android_2() = runTest {}

    @Test fun cloud_login_stores_jwt_and_shows_home() {}

    @Test
    @Ignore("flaky")
    fun `dry run header sent in test mode`() {}

    private fun helper_not_a_test() {}
}
"""


class JUnitTitlesTest(unittest.TestCase):
    """Les tests Kotlin/JUnit (Android) comptent pour coverage_must_test (tests.junit)."""

    def titles(self) -> list[str]:
        return [m.group("title").replace("_", " ") for m in gate.JUNIT_TITLE_PATTERN.finditer(KOTLIN)]

    def test_extracts_only_test_functions(self) -> None:
        titles = self.titles()
        self.assertEqual(len(titles), 3)
        self.assertNotIn("helper not a test", titles)

    def test_requirements_match_kotlin_titles(self) -> None:
        titles = self.titles()
        self.assertTrue(gate.title_matches("unauthorized response clears session and shows login", titles))
        self.assertTrue(gate.title_matches("cloud login stores jwt and shows home", titles))
        self.assertTrue(gate.title_matches("dry run header sent in test mode", titles))


SWIFT = """
struct AuthRepositoryTests {
    @Test func unauthorized_response_clears_session_and_shows_login_NR_ios_2() async {}
}
final class AppFlowUITests: XCTestCase {
    @MainActor func test_lan_host_in_cleartext_is_refused() {}
    private func login(_ app: XCUIApplication) {}
}
"""


class SwiftTitlesTest(unittest.TestCase):
    """Swift Testing (`@Test func`) et XCTest (`func test_…`) comptent pour coverage_must_test (iOS)."""

    def titles(self) -> list[str]:
        out = [m.group("title").replace("_", " ") for m in gate.JUNIT_TITLE_PATTERN.finditer(SWIFT)]
        out += [m.group("title").replace("_", " ") for m in gate.XCTEST_TITLE_PATTERN.finditer(SWIFT)]
        return out

    def test_swift_testing_and_xctest_titles(self) -> None:
        titles = self.titles()
        self.assertEqual(len(titles), 2)
        self.assertTrue(gate.title_matches("unauthorized response clears session and shows login", titles))
        self.assertTrue(gate.title_matches("lan host in cleartext is refused", titles))


class NativeMobileSurfaceTest(unittest.TestCase):
    def test_android_surface_skips_web_ux_matrix(self) -> None:
        manifest = {"implementation": {"primary_surface": "android", "paths": ["app/src/main/PortalRepository.kt"]}}
        self.assertFalse(gate.is_ui_feature(manifest))

    def test_web_surface_still_requires_ux_matrix(self) -> None:
        self.assertTrue(gate.is_ui_feature({"implementation": {"primary_surface": "react-user", "paths": []}}))


if __name__ == "__main__":
    unittest.main()
