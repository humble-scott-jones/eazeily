# Eazeily Core - Headless API for Technical Content Verification

**Eazeily Core** is a clean, headless backend API that validates AI-generated content for technical accuracy using the Google Gemini API. It's designed as a lean microservice that can be deployed on dedicated hardware infrastructure.

## Architecture

- **Modular & Typed**: Pure Python with strict type hints (TypedDict)
- **Gemini-First**: Uses Google Gemini 2.0 Flash for deterministic fact-checking
- **Headless**: No UI dependencies; JSON-in/JSON-out API
- **Observable**: Structured logging with execution metrics
- **Testable**: 100% unit test coverage for core logic

## Quick Start

### 1. Setup Environment

```bash
cd eazeily-core
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your Gemini API key
export GENAI_API_KEY="your-key-here"
```

### 3. Run Tests

```bash
pytest -v
```

### 4. Start Server (Development)

```bash
python3 -m api.server
```

Server listens on `http://localhost:8000`

## API Contract

### POST `/verify`

**Request:**
```json
{
  "draft_text": "The Commodore 64 uses a 6502 processor...",
  "niche_context_id": "vintage_computing"
}
```

**Response:**
```json
{
  "is_valid": false,
  "flagged_terms": [
    {
      "term": "6502",
      "suggested_fix": "6510",
      "severity": "critical"
    }
  ],
  "revised_draft": "The Commodore 64 uses a 6510 processor...",
  "confidence_score": 0.92,
  "execution_time_ms": 1245
}
```

## Environment Variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `GENAI_API_KEY` | ✅ Yes | — | Google Gemini API key from https://aistudio.google.com/app/apikey |
| `GOOGLE_API_KEY` | ❌ Alternative | — | Can be used instead of GENAI_API_KEY |
| `LOG_LEVEL` | ❌ No | `INFO` | DEBUG, INFO, WARNING, ERROR |
| `PORT` | ❌ No | `8000` | Server port |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_core_verification_engine.py -v
```

## Deployment

### Local/Development
```bash
python3 -m api.server
```

### Production (Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:8000 api.server:app
```

### Docker
```bash
docker build -t eazeily-core .
docker run -e GENAI_API_KEY=$GENAI_API_KEY -p 8000:8000 eazeily-core
```

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **Python + FastAPI** | Lean, fast, great for microservices |
| **TypedDict over Pydantic** | Zero-dependency for minimal size |
| **Gemini API** | Supports fact-checking + JSON output natively |
| **Deterministic Prompts** | Temperature=0 for reproducible results |
| **No ORM/DB** | Stateless API; Source of Truth is read-only JSON |

## License

Proprietary - Eazeily 2025
