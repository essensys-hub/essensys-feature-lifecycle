name: Security Gate

on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

jobs:
  security-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: python3 -m pip install --disable-pip-version-check pip-audit bandit
      - run: mkdir -p .artifacts/security-gate
      - name: CVE / SCA + IaC scan (Trivy)
        continue-on-error: true
        uses: aquasecurity/trivy-action@0.28.0
        with:
          scan-type: fs
          scan-ref: .
          format: json
          output: .artifacts/security-gate/trivy.json
          severity: CRITICAL,HIGH,MEDIUM
          scanners: vuln,misconfig
          ignore-unfixed: true
          exit-code: "0"
      - run: python3 scripts/feature_lifecycle/summarize_security_gate.py || true
