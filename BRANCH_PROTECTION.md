# Branch protection quick setup

Use the provided script to enable the "CI gating on `main`" step without clicking through the GitHub UI. It applies protection with required checks that match `.github/workflows/ci.yml` and prevents force-pushes or direct pushes to `main`.

## Prerequisites
- GitHub CLI installed (`https://cli.github.com/`) and authenticated: `gh auth login`
- `jq` installed
- Permissions to edit branch protection rules for the repository

## One-time setup
```bash
# From the repo root
./scripts/apply_branch_protection.sh
```
This applies protection to `main` with required checks:
- `CI / secret-scan`
- `CI / tests`
- `CI / triage-smoke`
- `CI / smoke`

## Customizing
- Protect a different branch: `BRANCH_PROTECTION_BRANCH=develop ./scripts/apply_branch_protection.sh`
- Override required checks: `BRANCH_PROTECTION_CHECKS="CI / tests,CI / smoke" ./scripts/apply_branch_protection.sh`
- Supply the repo explicitly (useful in forks/CI): `GITHUB_REPOSITORY=owner/repo ./scripts/apply_branch_protection.sh`

After running, verify in the GitHub UI under **Settings → Branches** that protection is enabled and the required checks match the ones you expect.
