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


GO = """
package support

// NR: NR-backend-3 essensys-hub/essensys-feature-lifecycle#15
func TestNR_backend_3_sixth_report_in_24h_is_429(t *testing.T) {}

func TestCreateBug_OpensAnonymisedPublicIssue(t *testing.T) {}

func BenchmarkX(b *testing.B) {}
func helperTest(t *testing.T) {}
"""


class GoTitlesTest(unittest.TestCase):
    """Les tests Go (`func TestXxx(t *testing.T)`) comptent pour coverage_must_test (backend)."""

    def titles(self) -> list[str]:
        return [gate.go_title(m.group("title")) for m in gate.GO_TEST_TITLE_PATTERN.finditer(GO)]

    def test_extracts_only_go_tests(self) -> None:
        titles = self.titles()
        self.assertEqual(len(titles), 2)
        self.assertEqual(gate.normalize(titles[1]), ["create", "bug", "opens", "anonymised", "public", "issue"])

    def test_requirements_match_go_titles(self) -> None:
        titles = self.titles()
        self.assertTrue(gate.title_matches("sixth report in 24h is 429", titles))
        self.assertTrue(gate.title_matches("create bug opens anonymised public issue", titles))


class SurfaceTest(unittest.TestCase):
    """Une feature `api` d'un dépôt nommé « …-portal-backend » n'est pas une UI."""

    def manifest(self, primary: str) -> dict:
        return {
            "implementation": {"primary_surface": primary, "paths": ["internal/support/routes.go"]},
            "release": {"surfaces": ["essensys-user-portal-backend"]},
        }

    def test_api_surface_is_not_ui(self) -> None:
        self.assertFalse(gate.is_ui_feature(self.manifest("api")))

    def test_mixed_surface_is_ui(self) -> None:
        self.assertTrue(gate.is_ui_feature(self.manifest("mixed")))

    def test_undeclared_surface_falls_back_to_path_hints(self) -> None:
        self.assertTrue(gate.is_ui_feature(self.manifest(None)))
