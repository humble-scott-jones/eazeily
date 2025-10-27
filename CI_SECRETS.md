CI non-production secrets (for repository settings)

These are safe, test-only values you should add to the repository's GitHub Secrets so Actions jobs that expect them won't crash before tests or fixtures can apply mocks.

Secrets to add (non-production test values):

- SECRET_KEY = ci-default-secret
- STRIPE_SECRET_KEY = sk_test_dummy
- STRIPE_PUBLISHABLE_KEY = pk_test_dummy
- STRIPE_PRICE_ID = price_test_dummy
- STRIPE_WEBHOOK_SECRET = whsec_dummy
- ADMIN_EMAILS = admin@example.com

Why: Some parts of the Flask app (and imported libraries) expect these env vars early during app import. Tests may monkeypatch values later, but supplying safe defaults prevents crashes during app startup in CI.

How to add them via GitHub CLI (replace owner/repo if different):

# Example (macOS/zsh):
# Install GitHub CLI and authenticate: https://cli.github.com/
# Then run:

gh secret set SECRET_KEY -b"ci-default-secret" --repo humble-scott-jones/togetherly
gh secret set STRIPE_SECRET_KEY -b"sk_test_dummy" --repo humble-scott-jones/togetherly
gh secret set STRIPE_PUBLISHABLE_KEY -b"pk_test_dummy" --repo humble-scott-jones/togetherly
gh secret set STRIPE_PRICE_ID -b"price_test_dummy" --repo humble-scott-jones/togetherly
gh secret set STRIPE_WEBHOOK_SECRET -b"whsec_dummy" --repo humble-scott-jones/togetherly
gh secret set ADMIN_EMAILS -b"admin@example.com" --repo humble-scott-jones/togetherly

If you prefer to add them in the GitHub UI:
1. Go to the repository on GitHub
2. Settings -> Security -> Secrets and variables -> Actions
3. Click 'New repository secret' and add each key/value above.

Notes:
- These are test values only — do NOT use them in production.
- Workflows in this repo already fall back to safe defaults when secrets are missing, but adding them reduces early startup failures and improves logs.
