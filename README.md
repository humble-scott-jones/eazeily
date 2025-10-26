# Togetherly (dev)

Run dev server:
```bash
source .venv/bin/activate
PORT=5001 python3 app.py
```

Run tests:
```bash
source .venv/bin/activate
PYTHONPATH=. pytest -q
# or run the helper script
./run_tests.sh
```

Run UI smoke tests (requires server running on port 5001). These are gated so they don't run by default during local development. Set the env var RUN_UI_SMOKE=1 to enable them.
```bash
# run unit tests only
PYTHONPATH=. pytest -q

# run UI smoke tests
RUN_UI_SMOKE=1 PYTHONPATH=. pytest -q
```

## Supported Industries

Togetherly supports the following industries with tailored content templates, hashtags, and tone:

- 🏡 Realtor / Real Estate
- 🍽️ Restaurant / Café
- 🛍️ Retail / Boutique
- 💪 Fitness / Wellness
- 🎨 Artisan / Maker
- 🧭 Coach / Consultant
- 🤝 Nonprofit / Community
- 🛠️ Home Services
- 🩺 Healthcare
- ⛪ Church
- ✨ Other / Custom

Each industry includes:
- Industry-specific suggested keywords
- Customized content pillars and templates
- Platform-specific post formats
- Reel/video content styles tailored to the industry

Industry configurations are located in `/static/content/config.json`.
