# Brand Profile Scraper - Manual Testing Guide

This guide explains how to manually verify that the Brand Profile Scraper is working correctly.

## Quick Test: Integration Test Suite

The fastest way to verify the implementation:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run integration tests
python -m pytest tests/test_scraper_profile_integration.py -v

# All tests should pass:
# ✅ test_scraper_integration_with_profile_save
# ✅ test_scraper_extracts_keywords (may skip if no AI key)
# ✅ test_profile_api_handles_missing_keywords_gracefully
```

## Manual Verification Script

Test the scraper with a real URL:

```bash
# Activate virtual environment
source .venv/bin/activate

# Set AI API key (required for keyword extraction)
export GENAI_API_KEY=your_api_key_here

# Run verification script
python manual_verify_scraper.py https://www.patagonia.com
```

Expected output:
```
Step 1: Scraping URL...
✅ Successfully scraped 5000 characters

Step 2: Extracting business information (including keywords)...
─────────────────────────────────────────────────
Extracted Business Information:
─────────────────────────────────────────────────
Business Name:     Patagonia
Industry:          Retail / Boutique
Key Customers:     Environmentally conscious outdoor enthusiasts

Brand Keywords:    sustainable, outdoor, quality, environmental
Niche Keywords:    outdoor apparel, climbing gear, activism, fair trade
─────────────────────────────────────────────────

✅ SUCCESS: Both brand_keywords and niche_keywords extracted
```

## Full End-to-End Test via API

1. **Start the server:**
```bash
PORT=5001 python3 app.py
```

2. **Create a test user:**
```bash
curl -X POST http://localhost:5001/api/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

3. **Use the onboarding scraper endpoint:**
```bash
curl -X POST http://localhost:5001/onboarding/social-style \
  -H "Content-Type: application/json" \
  -b cookies.txt -c cookies.txt \
  -d '{
    "url": "https://www.patagonia.com",
    "consent": true,
    "business_name": "Test Business"
  }'
```

Expected response should include:
```json
{
  "suggestions": {
    "business_name": "Patagonia",
    "industry": "Retail / Boutique",
    "key_customers": "...",
    "brand_keywords": ["sustainable", "outdoor", ...],
    "niche_keywords": ["outdoor apparel", ...]
  }
}
```

4. **Save profile with scraped data:**
```bash
curl -X POST http://localhost:5001/api/profile \
  -H "Content-Type: application/json" \
  -b cookies.txt -c cookies.txt \
  -d '{
    "company": "Patagonia",
    "industry": "Retail / Boutique",
    "brand_keywords": ["sustainable", "outdoor", "quality"],
    "niche_keywords": ["outdoor apparel", "climbing gear"],
    "target_audience": "Environmentally conscious outdoor enthusiasts"
  }'
```

5. **Retrieve and verify:**
```bash
curl http://localhost:5001/api/profile \
  -b cookies.txt | jq '.profile.brand_keywords, .profile.niche_keywords'
```

Expected output:
```json
["sustainable", "outdoor", "quality"]
["outdoor apparel", "climbing gear"]
```

## Checking for Interfering Features

✅ **Verified: No auto-generate features found**

We searched for automatic post-save behaviors that might interfere:
```bash
grep -rn "auto.*generat\|magic" routes/ services/
# Result: No interfering features found
```

The scraper:
- ✅ Only extracts data from URLs
- ✅ Does NOT automatically generate content
- ✅ Does NOT trigger post-save hooks
- ✅ Does NOT overwrite manual user input

## What Was Fixed

### Missing Fields Now Populated ✅
- ✅ `brand_keywords` - Extracted via AI from website content
- ✅ `niche_keywords` - Extracted via AI from website content
- ✅ `business_name` - Already working, now saved correctly
- ✅ `industry` - Already working, now saved correctly
- ✅ `key_customers` (mapped to target_audience) - Already working

### Profile API Created ✅
- ✅ `POST /api/profile` - Save profile data
- ✅ `GET /api/profile` - Retrieve profile data
- ✅ `GET /api/profile_v2` - Alternative format
- ✅ `POST /api/signup` - Alias for test compatibility

### Database Schema Extended ✅
- ✅ Added 10 new columns to `voice_profile` table
- ✅ Migration script created: `alembic/versions/20260110_add_brand_profile_fields.py`
- ✅ Helper methods for JSON serialization added

## Production Deployment Checklist

Before deploying to production:

1. **Run database migration:**
```bash
alembic upgrade head
```

2. **Set environment variables:**
```bash
export GENAI_API_KEY=your_production_key
export DATABASE_URL=your_postgres_connection_string
```

3. **Test scraper with real URLs:**
```bash
python manual_verify_scraper.py https://www.your-test-site.com
```

4. **Monitor logs for extraction accuracy:**
```bash
tail -f server.log | grep "Extracted business info"
```

## Troubleshooting

### Keywords not extracting?
- Check that `GENAI_API_KEY` is set
- Verify AI service is accessible
- Check logs for API errors

### Scraper returning None?
- Some sites block scrapers (check robots.txt)
- Try a different URL
- Check if site requires JavaScript (scraper uses static HTML)

### Profile not saving?
- Ensure user is logged in (check cookies)
- Verify database migration ran successfully
- Check server logs for errors
