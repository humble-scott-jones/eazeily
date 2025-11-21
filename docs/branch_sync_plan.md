# Branch Sync & Integration Plan (Nov 20, 2025)

This note captures the proposed approach for getting the active branches back in sync and preparing a pull request that harmonizes the most important changes.

## 1. Snapshot of active branches

| Branch | Upstream delta | Notes |
| --- | --- | --- |
| `main` | in sync with `origin/main` | Canonical production baseline. |
| `feature/add-logo` *(current)* | **ahead 4** | Contains the latest account/team-approval UI work, new tests, and assorted launch assets. |
| `feature/content-pack` | ahead 2 / behind 110 | Diverged significantly; contains earlier content-pack experiments. |
| `feature/db-compat` | tracking | Adds SQLite vs swelly DB compatibility helpers. |
| `feature/phase2-reels` | remote gone | Can likely be archived or re-created by cherry-picking if still needed. |
| `split/*`, `wip/*` | mixed | Snapshot branches from Oct 2025; should be treated as archival unless a specific change is required. |

## 2. Recommended integration strategy

1. **Create an integration branch** `integration/2025-11-sync` off `origin/main`.
2. **Merge `feature/add-logo` first** since it carries the most recent launch-critical work (team approvals, admin UI, CI/test adjustments). Resolve conflicts locally and ensure `pytest -q` passes (already green in this workspace).
3. **Triage the other branches**:
   - For branches that are *ahead but also behind* (e.g., `feature/content-pack`), decide whether to cherry-pick specific commits or reapply the work on top of the new integration branch. These branches are so far behind that a direct merge will be noisy.
   - For infra branches (`chore/deploy-railway`, `chore/deploy-appengine`, `feature/db-compat`), merge one at a time into the integration branch, running targeted smoke tests (e.g., `scripts/feedback_smoke.sh`, deployment dry-runs) between merges.
   - For archival branches (`split/*`, `wip/*`), capture any remaining TODOs in GitHub issues and delete them once confirmed.
4. **Open a PR** from `integration/2025-11-sync` → `main`. Use the PR to:
   - Document the staged merge order and validation artifacts.
   - Reference any follow-up issues (e.g., re-run e2e tests, update docs) needed after merge.
   - Include the test evidence (`pytest -q`, manual `/healthz`, etc.).
5. **After merge**, delete the integrated branches or tag them for reference, then rebase any still-active feature work on top of the updated `main`.

## 3. Checklist for the sync PR

- [x] Merge `feature/add-logo` and ensure `pytest -q` passes.
- [ ] Verify Stripe/OpenAI env handling on staging (requires secrets from Priority 0 checklist).
- [ ] Run `scripts/feedback_smoke.sh --start-local` (gated on env vars) once secrets are available.
- [ ] Confirm `static/dashboard.js` and new templates render with the team-approval feature flags toggled both on/off.
- [ ] Capture screenshots or Loom showing the refreshed account page + approvals admin view.
- [ ] Update `docs/changelog.md` with the integration summary.

## 4. Risks & mitigations

- **Large diff surface (12k LOC)** – mitigate by merging in stages on the integration branch and leaning on automated tests.
- **Stale feature branches** – prefer cherry-picking specific commits rather than wholesale merges when divergence >2 weeks.
- **Secrets/Deploy gaps** – coordinate with the Priority 0 checklist to ensure GitHub + Railway secrets exist before deploying from the synced branch.

## 5. Next steps

1. Push `feature/add-logo` and open PR if not already done.
2. Cut `integration/2025-11-sync` from `origin/main` and merge `feature/add-logo` into it.
3. Sequentially merge the remaining high-value branches, validating between each merge as outlined above.
4. Finalize the integration PR with test artifacts and request review.

## 6. Execution log (Nov 20, 2025)

- ✅ `feature/add-logo` staged + committed (`3eb2579`) with team approval UI, tests, and planning docs.
- ✅ Created `integration/2025-11-sync` from `origin/main`, merged `feature/add-logo`, and pushed to GitHub (`origin/integration/2025-11-sync`).
- ✅ Test coverage: `pytest -q` (passes with expected `NotOpenSSLWarning`).
- ✅ Safety branch `integration/2025-11-sync-content-pack` created to experiment with `feature/content-pack` merge; initial direct merge revealed wide conflicts (`app.py`, templates, tests, workflows). Plan is to cherry-pick the two unique commits (`14cdc43`, `7803bd9`) or re-apply the minimal deltas manually to avoid destabilizing the new integration branch.
