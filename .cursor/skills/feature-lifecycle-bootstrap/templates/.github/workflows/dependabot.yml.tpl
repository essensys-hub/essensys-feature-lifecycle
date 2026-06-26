# Dependabot configuration template — GitHub-native Software Composition Analysis.
# Install this as `.github/dependabot.yml` (NOT under .github/workflows/).
# Keep only the ecosystems and directories that exist in the target repo.
# Reference: https://docs.github.com/code-security/dependabot
version: 2
updates:
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: weekly
    labels:
      - security
      - dependencies

  # Uncomment per detected stack:
  # - package-ecosystem: pip
  #   directory: "/"
  #   schedule:
  #     interval: weekly
  #   labels: [security, dependencies]

  # - package-ecosystem: npm
  #   directory: "/"
  #   schedule:
  #     interval: weekly
  #   labels: [security, dependencies]
