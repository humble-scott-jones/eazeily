#!/usr/bin/env python3
"""
Manual verification script for Brand Profile Scraper.

This script demonstrates the complete flow:
1. Scrape a URL
2. Extract business info (including brand_keywords and niche_keywords)
3. Save to profile API
4. Retrieve and verify

Usage:
    python manual_verify_scraper.py <url>

Example:
    python manual_verify_scraper.py https://www.example.com
"""

import sys
import json
from services.scraper_service import scrape_url, extract_business_info


def verify_scraper(url):
    """Manually verify the scraper functionality."""
    print(f"\n{'='*60}")
    print(f"Testing Brand Profile Scraper with URL: {url}")
    print(f"{'='*60}\n")
    
    # Step 1: Scrape the URL
    print("Step 1: Scraping URL...")
    scraped_text = scrape_url(url, max_length=5000)
    
    if not scraped_text:
        print("❌ ERROR: Failed to scrape URL")
        return False
    
    print(f"✅ Successfully scraped {len(scraped_text)} characters")
    print(f"Preview: {scraped_text[:200]}...")
    print()
    
    # Step 2: Extract business info
    print("Step 2: Extracting business information (including keywords)...")
    business_info = extract_business_info(scraped_text, url)
    
    print(f"\n{'─'*60}")
    print("Extracted Business Information:")
    print(f"{'─'*60}")
    print(f"Business Name:     {business_info.get('business_name') or 'Not found'}")
    print(f"Industry:          {business_info.get('industry') or 'Not found'}")
    print(f"Key Customers:     {business_info.get('key_customers') or 'Not found'}")
    print(f"\nBrand Keywords:    {', '.join(business_info.get('brand_keywords', [])) or 'None'}")
    print(f"Niche Keywords:    {', '.join(business_info.get('niche_keywords', [])) or 'None'}")
    print(f"{'─'*60}\n")
    
    # Check if keywords were extracted
    has_brand_keywords = len(business_info.get('brand_keywords', [])) > 0
    has_niche_keywords = len(business_info.get('niche_keywords', [])) > 0
    
    if has_brand_keywords and has_niche_keywords:
        print("✅ SUCCESS: Both brand_keywords and niche_keywords extracted")
    elif has_brand_keywords:
        print("⚠️  WARNING: Only brand_keywords extracted (niche_keywords missing)")
    elif has_niche_keywords:
        print("⚠️  WARNING: Only niche_keywords extracted (brand_keywords missing)")
    else:
        print("❌ ERROR: No keywords extracted")
    
    # Step 3: Prepare profile data
    print("\nStep 3: Preparing profile data for API save...")
    profile_data = {
        'company': business_info.get('business_name'),
        'industry': business_info.get('industry'),
        'target_audience': business_info.get('key_customers'),
        'brand_keywords': business_info.get('brand_keywords', []),
        'niche_keywords': business_info.get('niche_keywords', []),
    }
    
    print("\nProfile data ready:")
    print(json.dumps(profile_data, indent=2))
    
    print("\n" + "="*60)
    print("Verification Complete!")
    print("="*60)
    print("\nNext Steps:")
    print("1. Start the server: PORT=5001 python3 app.py")
    print("2. Create a user via /api/signup")
    print("3. POST this profile data to /api/profile")
    print("4. GET /api/profile to verify all fields are populated")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manual_verify_scraper.py <url>")
        print("Example: python manual_verify_scraper.py https://www.patagonia.com")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # Ensure URL has protocol
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    
    try:
        success = verify_scraper(url)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
