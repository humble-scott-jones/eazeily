# Branching & PR Hygiene

- Branch from `main`; keep branches short-lived (<3 days). Naming: `feature/<slug>`, `fix/<slug>`, `chore/<slug>`.
- Rebase against `main` before opening a PR and again before merge to keep histories linear.
- Prefer fast-forward merges into `main`; avoid merge commits unless backporting or resolving multi-branch work.
- Keep PRs small and scoped. Use the PR template and update the checklist (tests, migrations, changelog, rollback notes).
- If a PR is noisy/conflict-prone, cut a fresh branch from `main`, cherry-pick the commits, and close the old branch.
- Update `docs/changelog.md` with what’s landing in staging vs production as you merge to `main`.
