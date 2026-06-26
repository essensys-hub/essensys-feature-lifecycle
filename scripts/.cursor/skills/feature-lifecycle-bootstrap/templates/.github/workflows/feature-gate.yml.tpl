name: Feature Gate

on:
  pull_request:
    branches: [main]
    paths:
      - "features/**"
      - "openspec/changes/**"
      - "docs/features/**"
      - "tests/**"
      - "scripts/feature_lifecycle/**"

permissions:
  contents: read
  pull-requests: write

jobs:
  feature-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python3 -m pip install --disable-pip-version-check jsonschema
      - run: python3 scripts/feature_lifecycle/validate_feature_manifests.py || true
      - run: python3 scripts/feature_lifecycle/check_feature_gate.py || true
