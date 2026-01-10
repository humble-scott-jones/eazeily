import requests
from bs4 import BeautifulSoup
import logging
import re
import json

logger = logging.getLogger(__name__)

# Industry categories that match the onboarding form options
INDUSTRY_CATEGORIES = [
    "Software / Tech / Startup",
    "Realtor / Real Estate",
    "Restaurant / Café",
    "Retail / Boutique",
    "Fitness / Wellness",
    "Artisan / Maker",
    "Coach / Consultant",
    "Nonprofit / Community",
    "Home Services",
    "Healthcare",
    "Church",
    "House Host / Vacation Rental",
    "Other / Custom"
]

def scrape_url(url: str, max_length: int = 5000) -> str:
    """
    Fetches the content of a URL and returns the visible text.
    
    Args:
        url (str): The URL to scrape.
        max_length (int): Maximum number of characters to return.
        
    Returns:
        str: Cleaned text content from the webpage, or None if failed.
    """
    try:
        # User agent to avoid some basic bot blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script, style, and navigation elements that corrupt text context
        for element in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
            element.extract()
            
        # Get text
        text = soup.get_text(separator=' ')
        
        # Clean up whitespace
        # 1. Replace multiple spaces/tabs with single space
        text = re.sub(r'\s+', ' ', text)
        # 2. Trim
        text = text.strip()
        
        if not text:
            return None
            
        return text[:max_length]
        
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return None


def extract_business_info(scraped_text: str, url: str = "") -> dict:
    """
    Uses AI to extract business name, industry, and key customers from scraped text.
    
    Args:
        scraped_text (str): The text content from the webpage.
        url (str): The URL of the webpage (optional, for context).
        
    Returns:
        dict: Contains business_name, industry, and key_customers fields.
              Returns None values if extraction fails or AI is unavailable.
    """
    try:
        from services.ai_service import get_generative_model
        
        model = get_generative_model()
        if not model:
            logger.warning("AI service not available for business info extraction")
            return {
                "business_name": None,
                "industry": None,
                "key_customers": None
            }
        
        # Limit text length for AI processing
        text_sample = scraped_text[:3000] if len(scraped_text) > 3000 else scraped_text
        
        # Format industry categories as properly quoted strings
        industries_list = ', '.join(json.dumps(cat) for cat in INDUSTRY_CATEGORIES)
        
        prompt = f"""Analyze the following website content and extract business information. Return ONLY a JSON object with these exact keys:

- business_name: The company/business name (string, or null if not found)
- industry: The business industry category - pick ONE that best matches from this list: {industries_list} (string, or null if not clear)
- key_customers: A brief description of the target audience/customers in 1-2 sentences (string, or null if not found)

Website content:
{text_sample}

Return only valid JSON, no markdown formatting, no explanations."""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON response
        extracted_data = json.loads(response_text)
        
        # Validate and clean the extracted data
        result = {
            "business_name": extracted_data.get("business_name") or None,
            "industry": extracted_data.get("industry") or None,
            "key_customers": extracted_data.get("key_customers") or None
        }
        
        logger.info("Successfully extracted business info from scraped text")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        return {
            "business_name": None,
            "industry": None,
            "key_customers": None
        }
    except Exception as e:
        logger.error(f"Failed to extract business info: {e}")
        return {
            "business_name": None,
            "industry": None,
            "key_customers": None
        }
