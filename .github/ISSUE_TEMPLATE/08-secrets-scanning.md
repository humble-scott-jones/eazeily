---
name: 🔒 Must-Have 8 - Secrets Scanning and Commit Protection
about: Automated secrets scanning with gitleaks or similar tools
title: '[LAUNCH] Secrets Scanning and Commit Protection'
labels: ['launch', 'security', 'high-priority', 'infra']
assignees: []
---

## Priority
**Must-Have #8** - Complete before launch

## Description
Implement automated secrets scanning using gitleaks or similar tools to prevent accidental commit of sensitive credentials. Scans should run on PRs and nightly.

## Acceptance Criteria
- [ ] Gitleaks (or equivalent) runs on all PRs
- [ ] Nightly scans of entire repository
- [ ] Secret leaks detected are blocked/flagged
- [ ] Pre-commit hooks available for developers
- [ ] Historical scan completed and remediated
- [ ] Scan results integrated with security dashboard
- [ ] Team trained on handling detected secrets

## Implementation Tasks
- [ ] Add gitleaks GitHub Action to CI workflow
- [ ] Configure gitleaks rules and exceptions
- [ ] Set up nightly scheduled scan
- [ ] Create pre-commit hook for local development
- [ ] Run initial full repository scan
- [ ] Remediate any found secrets
- [ ] Configure PR blocking on secret detection
- [ ] Set up notifications for detected secrets
- [ ] Document secret remediation procedures
- [ ] Create runbook for handling leaked secrets

## GitHub Action Configuration

```yaml
# Add to .github/workflows/security.yml
name: Security Scanning

on:
  pull_request:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Pre-commit Hook Setup

```bash
# Install gitleaks locally
brew install gitleaks  # macOS
# or download from releases

# Add to .git/hooks/pre-commit
gitleaks detect --source . --verbose
```

## Secret Types to Detect
- API keys (OpenAI, Stripe, etc.)
- Database credentials
- JWT secrets
- OAuth tokens
- SSH private keys
- Cloud provider credentials
- Third-party service tokens

## Current State
- ⚠️ No automated secrets scanning
- ⚠️ Need historical scan
- ⚠️ Need CI integration

## Dependencies
- CI workflow (#2)

## Resources
- [Gitleaks](https://github.com/gitleaks/gitleaks)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)
- [TruffleHog](https://github.com/trufflesecurity/trufflehog)

## Definition of Done
- All acceptance criteria met
- Gitleaks running in CI
- Historical scan completed
- No unresolved secret leaks
- Team trained on prevention
