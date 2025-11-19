# Priority 0 Runbook – Feedback Pipeline, CI Gating, and Smoke Tests

This runbook turns the highest-priority launch blockers into concrete checklists. Follow the three sections below (in order) to unlock the feedback → GitHub automation and protect the `main` branch.

> **Scope**
> 1. Wire secrets/credentials for production + staging.
> 2. Enable CI gating and branch protection on `main`.
> 3. Run a full feedback smoke test (thumbs-down + settings feedback) against staging.

---

## 1. Secrets & Credentials

### 1.1 Inventory required environment variables

| Category | Keys |
| --- | --- |
| Core Flask | `SECRET_KEY`, `FLASK_ENV`, `PORT`, `ADMIN_EMAILS`, `ALLOW_DEV_DEBUG` (dev only) |
| Database | `DB_PATH` (local) **or** managed database URL + credentials (prod/staging) |
| Stripe | `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_PRICE_ID` (and `STRIPE_TEST_PRICE_ID` if you keep the legacy fallback), optional `STRIPE_WEBHOOK_SECRET` |
| OpenAI (optional) | `OPENAI_API_KEY`, `OPENAI_GENERATE_MODEL` |
| Feedback automation | `GITHUB_FEEDBACK_TOKEN`, `GITHUB_FEEDBACK_REPO`, `GITHUB_FEEDBACK_TEMPLATE_GENERAL`, `GITHUB_FEEDBACK_TEMPLATE_THUMBSDOWN`, `GITHUB_FEEDBACK_TIMEOUT` |
| Misc | `TEAM_MEMBER_LIMIT`, `REELS_QUOTA_MONTHLY`, `DEV_ADMIN_PW` (local dev only) |

> Tip: Keep the authoritative list in `.env.example`. A `scripts/check_env.py` hook (planned later) can warn when keys are missing locally.

### 1.2 Create secrets in your manager of choice

1. Pick a manager (1Password Secrets Automation, Doppler, AWS Secrets Manager, Render/Fly dashboard, etc.).
2. Create **two** stacks: `togetherly-staging` and `togetherly-prod`.
3. Store all keys above. For GitHub automation:
   - `GITHUB_FEEDBACK_TOKEN`: Fine-grained PAT scoped to the feedback repository with `Issues: Read/Write`.
   - `GITHUB_FEEDBACK_REPO`: `humble-scott-jones/swelly` (or your fork).
   - Optional: set the template names if you customize `.github/ISSUE_TEMPLATE` files.
4. Document rotation owners + cadence in your secret manager notes.

### 1.3 Export secrets for local smoke tests

```bash
# Example using 1Password CLI
eval "$(op plugin init)"
op inject -i .env.example -o .env.feedback-smoke
```

Verify sensitive files remain ignored (see `.gitignore`).

---

## 2. CI Gating & Branch Protection

The workflow `.github/workflows/ci.yml` produces two key status checks:
- `tests` (Python 3.10 + 3.11 matrix)
- `smoke` (UI + API smoke after unit tests pass)

### 2.1 Require status checks & reviews

Use the GitHub UI **or** the CLI recipe below (requires `gh` CLI and admin permissions):

```bash
# Replace OWNER/REPO as needed
OWNER=humble-scott-jones
REPO=swelly

gh api -X PUT \
  repos/$OWNER/$REPO/branches/main/protection \
  -F required_status_checks.strict=true \
  -F required_status_checks.contexts[]='tests' \
  -F required_status_checks.contexts[]='smoke' \
  -F enforce_admins=true \
  -F required_pull_request_reviews.dismiss_stale_reviews=true \
  -F required_pull_request_reviews.required_approving_review_count=1 \
  -F restrictions=null
```

### 2.2 Block force pushes & direct merges

Still in the branch protection UI:
- Enable **“Require a pull request before merging.”**
- Disable **“Allow force pushes.”**
- Disable **“Allow deletions.”**

### 2.3 Add CODEOWNERS (optional next step)

Create a `.github/CODEOWNERS` file assigning at least one reviewer group. This guarantees every PR requests a reviewer automatically and keeps branch protection effective.

---

## 3. Feedback → GitHub Smoke Test

Use the new helper script `scripts/feedback_smoke.sh` to validate end-to-end automation in staging or a local tunnel.

### 3.1 Prepare env file

```bash
cp .env.example .env.feedback-smoke
# edit .env.feedback-smoke with:
# - real Stripe/OpenAI keys (or leave blank if not testing those paths)
# - GITHUB_FEEDBACK_TOKEN (PAT)
# - GITHUB_FEEDBACK_REPO (e.g. humble-scott-jones/swelly)
# - ADMIN_EMAILS with your staging user
```

### 3.2 Run the script

```bash
./scripts/feedback_smoke.sh --env .env.feedback-smoke --base-url https://staging.swelly.app
```

The script:
1. Optionally starts a local server (when `--base-url` is omitted).
2. Posts a thumbs-down feedback sample (rating `-1`) and ensures a GitHub issue is returned.
3. Posts a Settings feedback report and verifies the API returns 200.
4. Prints the issue URLs so you can confirm labels + templates.

### 3.3 Troubleshooting

- Missing PAT ➜ script aborts before sending payloads.
- PAT lacks repo scope ➜ GitHub API returns 401/403 (script surfaces response body).
- Templates renamed ➜ set `GITHUB_FEEDBACK_TEMPLATE_GENERAL` and `GITHUB_FEEDBACK_TEMPLATE_THUMBSDOWN` in the env file.
- Rate limits ➜ increase `GITHUB_FEEDBACK_TIMEOUT` (seconds) or try again after 60 seconds.

Document the outcome (issue URLs + timestamp) in your launch tracker. Once all three sections are complete, mark “Priority 0” as ✅ in `LAUNCH_NEXT_STEPS.md`.
