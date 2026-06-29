name: UX Matrix Gate

on:
  pull_request:
    branches: [main]
    paths:
      - "src/pages/**"
      - "src/components/**"
      - "e2e/**"
      - "tests/e2e/**"
      - "features/**"
      - "playwright.config.*"
      - "package.json"
      - "package-lock.json"
      - "pnpm-lock.yaml"
      - "yarn.lock"

permissions:
  contents: read

jobs:
  ux-matrix:
    name: UX matrix desktop+iPhone+iPad
    runs-on: ubuntu-latest
    env:
      ESSENSYS_TEST_MODE: dry-run
      PLAYWRIGHT_HTML_REPORT: playwright-report
    steps:
      - name: Checkout
        uses: actions/checkout@v7

      - name: Set up Node
        uses: actions/setup-node@v6
        with:
          node-version: "22"
          cache: npm

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: List Playwright projects
        run: npx playwright test --list

      - name: Run mandatory UX matrix
        run: |
          npx playwright test \
            --project=support-desktop \
            --project=support-iphone \
            --project=support-ipad

      - name: Upload Playwright report
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: ux-matrix-playwright-report
          path: playwright-report/
          retention-days: 14

      - name: Upload screenshots and snapshots
        if: always()
        uses: actions/upload-artifact@v7
        with:
          name: ux-matrix-visual-artifacts
          path: |
            test-results/
            e2e/artifacts/screenshots/
            **/*-snapshots/
          retention-days: 14
