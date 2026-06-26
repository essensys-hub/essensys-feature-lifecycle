"""PAGE_TREE for the Skills Portal `docs` target.

Loaded by `confluence_publish.py` (multi-target Confluence publisher) when
`.confluence.json[targets][docs].page_tree_module = "scripts.page_tree"`.

Each node maps a docs file (relative to `docs/`) to an English Confluence
page title. The root title is used as a prefix for child pages
(e.g. "Skills Portal — Architecture").
"""
from __future__ import annotations

PAGE_TREE: list[dict] = [
    {"title": "Skills Portal", "file": "README.md", "children": [
        {"title": "Architecture — Index", "file": "architecture/README.md"},
        {"title": "Architecture — Overview", "file": "architecture/overview.md"},
        {"title": "Architecture — C4 Diagrams", "file": "architecture/c4.md"},
        {"title": "Data Model", "file": "architecture/data.md"},
        {"title": "Application Flows", "file": "architecture/flows.md"},
        {"title": "Deployment (EKS + Posit Connect)", "file": "architecture/deployment.md"},
        {"title": "Security and Access Control", "file": "architecture/security.md"},
        {"title": "KMS Setup for Signing", "file": "architecture/kms-setup.md"},
        {"title": "Git Workflow and CI/CD", "file": "git-workflow.md"},
        {"title": "API Reference", "file": "api-reference.md"},
        {"title": "Admin UI", "file": "admin-ui.md"},
        {"title": "CLIs (Go + Node.js)", "file": "cli.md"},
        {"title": "Backup and Restore", "file": "backup-restore.md"},
        {"title": "Operations and Runbooks", "file": "operations.md"},
        {"title": "CodeGuard Scan Analysis (Archived — superseded by Dependabot SCA)", "file": "codeguard.md", "children": [
            {"title": "Scan 2026-04-24 — int-feature-config (Archived)", "file": "codeguard/scan-2026-04-24-int-feature-config.md"},
        ]},
        {"title": "Official Publish (CI/CD)", "file": "official_publish.md"},
        {"title": "ZIP Artifact Import", "file": "features/import-artifacts.md"},
        {"title": "User UI", "file": "features/user-ui.md"},
        {"title": "Files Viewer (read-only)", "file": "features/files-viewer.md"},
        {"title": "Feature Lifecycle Automation", "file": "features/feature-lifecycle.md", "children": [
            {"title": "Feature Lifecycle — Quick Start", "file": "feature-lifecycle/README.md"},
            {"title": "Feature Lifecycle — Start Empty Project", "file": "feature-lifecycle/init-empty-project.en.md"},
            {"title": "Feature Lifecycle — Add to Existing Project", "file": "feature-lifecycle/init-existing-project.en.md"},
            {"title": "Feature Lifecycle — Daily Workflow", "file": "feature-lifecycle/daily-workflow.en.md"},
            {"title": "Feature Lifecycle — Troubleshooting", "file": "feature-lifecycle/troubleshooting.en.md"},
        ]},
        {"title": "Skill Builder", "file": "features/skill-builder.md"},
        {"title": "Version Comparator", "file": "features/version-comparator.md"},
        {"title": "MindWise Scan Reports", "file": "features/scan-report.md"},
        {"title": "Profiles User Guide", "file": "features/profiles-user-guide.md"},
        {"title": "Multi-Agent Installation", "file": "features/install-multi-agent.md"},
        {"title": "Internationalization (i18n)", "file": "features/i18n.md"},
        {"title": "GitHub Issues", "file": "features/github-issues.md"},
        {"title": "Drafts Workflow", "file": "features/drafts-workflow.md"},
        {"title": "Coverage Matrix", "file": "features/coverage-matrix.md"},
        {"title": "Offline Registry", "file": "features/offline-registry.md"},
        {"title": "User Guide — End Users", "file": "UserGuideUser.md"},
        {"title": "User Guide — Administrators", "file": "UserGuideAdmin.md"},
        {"title": "ADR — Architecture Decision Records", "file": "architecture/adr/README.md", "children": [
            {"title": "ADR-0001 — Backend on EKS", "file": "architecture/adr/0001-backend-on-eks.md"},
            {"title": "ADR-0002 — API Key for Writes", "file": "architecture/adr/0002-api-key-for-writes.md"},
            {"title": "ADR-0003 — Artifact Signing via KMS", "file": "architecture/adr/0003-skill-signing-with-kms.md"},
        ]},
        {"title": "Unit Tests", "file": "UnitTest/unit-test-catalog.md", "children": [
            {"title": "Unit Test Catalog", "file": "UnitTest/unit-test-catalog.md"},
            {"title": "UAT Test Report (Hash)", "file": "UnitTest/report-tests-unitaires-uat-hash.md"},
            {"title": "GxP Unit Test Report", "file": "UnitTest/gxp-unit-test-report-20260317T130423Z-5bd93ef.md"},
        ]},
    ]},
]
