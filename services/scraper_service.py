import logging
import re
import json
from collections import Counter
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

STOPWORDS = {
    'the', 'and', 'for', 'with', 'your', 'our', 'from', 'that', 'this', 'are',
    'was', 'were', 'will', 'you', 'your', 'yours', 'their', 'they', 'them',
    'we', 'us', 'about', 'into', 'over', 'under', 'on', 'in', 'of', 'to',
    'a', 'an', 'at', 'as', 'by', 'it', 'its', 'be', 'is', 'or', 'if', 'but'
}

GOAL_KEYWORDS = {
    "awareness/education": ["learn", "guide", "how it works", "how-to", "discover", "educat", "awareness"],
    "lead_gen/conversion": ["pricing", "start", "demo", "sign up", "book", "schedule", "get started", "try"],
    "retention/support": ["help", "docs", "faq", "support", "customer", "success", "care"]
}

CTA_KEYWORDS = ["sign up", "get started", "book", "schedule", "contact", "start", "try", "demo", "learn more", "join"]
BRAND_KEYWORD_LIMIT = 10

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


def _extract_domain_name(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if host.startswith("www."):
            host = host[4:]
        name_part = host.split(".")[0]
        if not name_part:
            return None
        return name_part.replace("-", " ").title()
    except Exception:
        return None


def _first_sentence(text: str) -> str | None:
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return parts[0].strip() if parts and parts[0].strip() else None


def _infer_industry(text: str) -> str | None:
    lowered = text.lower()
    industry_map = {
        "fitness": "Fitness / Wellness",
        "wellness": "Fitness / Wellness",
        "restaurant": "Restaurant / Café",
        "cafe": "Restaurant / Café",
        "coffee": "Restaurant / Café",
        "retail": "Retail / Boutique",
        "boutique": "Retail / Boutique",
        "real estate": "Realtor / Real Estate",
        "property": "Realtor / Real Estate",
        "church": "Church",
        "consult": "Coach / Consultant",
        "coach": "Coach / Consultant",
        "software": "Software / Tech / Startup",
        "tech": "Software / Tech / Startup",
        "startup": "Software / Tech / Startup",
    }
    for keyword, industry in industry_map.items():
        if keyword in lowered:
            return industry
    return None


def _extract_target_audience(text: str) -> list[str]:
    candidates = set()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    patterns = [
        r"\bfor ([A-Za-z0-9 ,&/-]{3,80})",
        r"\bbuilt for ([A-Za-z0-9 ,&/-]{3,80})",
        r"\bdesigned for ([A-Za-z0-9 ,&/-]{3,80})",
        r"\bteams of ([A-Za-z0-9 ,&/-]{3,80})",
    ]
    for sentence in sentences:
        lowered = sentence.lower()
        if any(token in lowered for token in ["for", "built for", "designed for", "teams of"]):
            for pat in patterns:
                match = re.search(pat, sentence, re.IGNORECASE)
                if match:
                    candidate = match.group(1).strip(" ,.-")
                    if candidate:
                        candidates.add(candidate)
    # Fallback: return distinct phrases split by commas if any exist
    if not candidates and "," in text[:200]:
        for chunk in text[:200].split(","):
            chunk = chunk.strip()
            if len(chunk) > 3:
                candidates.add(chunk)
    return list(candidates)


def _extract_key_offer(text: str) -> dict:
    offer = {"headline": None, "value_prop": None, "primary_cta": None}
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for sentence in sentences:
        lowered = sentence.lower()
        if any(k in lowered for k in CTA_KEYWORDS):
            offer["headline"] = offer["headline"] or sentence.strip()
            offer["value_prop"] = offer["value_prop"] or sentence.strip()
            for keyword in CTA_KEYWORDS:
                if keyword in lowered:
                    offer["primary_cta"] = keyword
                    break
            if offer["headline"] and offer["primary_cta"]:
                break
    return offer


def _extract_brand_keywords(text: str, existing: list[str] | None = None, limit: int = BRAND_KEYWORD_LIMIT) -> list[str]:
    words = re.findall(r'[A-Za-z]{4,}', text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    counts = Counter(filtered)
    keywords = [word for word, _ in counts.most_common(limit)]
    combined = (existing or []) + keywords
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for kw in combined:
        if kw and kw.lower() not in seen:
            deduped.append(kw)
            seen.add(kw.lower())
        if len(deduped) >= limit:
            break
    return deduped


def _extract_content_goals(text: str) -> list[dict]:
    lowered = text.lower()
    goals = []
    for goal, markers in GOAL_KEYWORDS.items():
        for marker in markers:
            if marker in lowered:
                goals.append({"goal": goal, "rationale": f"Found marker '{marker}'"})
                break
    return goals


def _build_required_sections(scraped_text: str, url: str, ai_data: dict) -> dict:
    text = scraped_text or ""
    domain_name = _extract_domain_name(url)
    inferred_industry = _infer_industry(text) or ai_data.get("industry")
    target_list = []
    if ai_data.get("key_customers"):
        # Split sentences into list items
        for chunk in re.split(r'[.;\n]', ai_data.get("key_customers")):
            cleaned = chunk.strip()
            if cleaned:
                target_list.append(cleaned)
    target_list.extend(_extract_target_audience(text))
    # Deduplicate
    target_list = list(dict.fromkeys([t for t in target_list if t]))

    key_offer_data = _extract_key_offer(text)
    if ai_data.get("key_offer"):
        key_offer_data["headline"] = key_offer_data["headline"] or ai_data.get("key_offer")
        key_offer_data["value_prop"] = key_offer_data["value_prop"] or ai_data.get("key_offer")

    brand_keywords = _extract_brand_keywords(text, ai_data.get("brand_keywords", []))
    content_goals = _extract_content_goals(text)

    # Merge AI content goals
    ai_goals = ai_data.get("content_goals_ai") or []
    if ai_goals:
        current_goals = {g['goal'].lower() for g in content_goals}
        for goal in ai_goals:
            if isinstance(goal, str) and goal.lower() not in current_goals:
                content_goals.append({"goal": goal, "rationale": "Identified by AI analysis"})
                current_goals.add(goal.lower())

    basic_information = {
        "name": ai_data.get("business_name") or domain_name,
        "description": ai_data.get("key_customers") or _first_sentence(text),
        "website": url or None,
        "industry": inferred_industry,
    }

    sections = {
        "basic_information": basic_information,
        "target_audience": {
            "values": target_list[:5],
        },
        "key_offer": key_offer_data,
        "brand_keywords": {
            "values": brand_keywords[:10],
        },
        "content_goals": {
            "values": content_goals,
        },
        "voice_profile": {
            "tone_guide": ai_data.get("voice_tone_and_style"),
            "sample_posts": ai_data.get("sample_posts", []),
        }
    }

    # Apply status/missing_reason to each section
    for key, payload in sections.items():
        if key == "target_audience":
            ok = bool(payload["values"])
        elif key == "brand_keywords":
            ok = bool(payload["values"])
        elif key == "content_goals":
            ok = bool(payload["values"])
        elif key == "voice_profile":
            ok = bool(payload["tone_guide"])
        else:
            ok = any(v for v in payload.values() if v)
        payload["status"] = "ok" if ok else "missing"
        if not ok:
            payload["missing_reason"] = "No matching patterns found in scraped text"
        else:
            payload["missing_reason"] = None

    missing_sections = [k for k, v in sections.items() if v.get("status") != "ok"]
    fill_rate = (len(sections) - len(missing_sections)) / max(len(sections), 1)
    validation = {
        "missing_sections": missing_sections,
        "fill_rate": fill_rate,
    }

    logger.info(
        "Scraper fill-rate %.0f%% | missing: %s",
        fill_rate * 100,
        ", ".join(missing_sections) if missing_sections else "none"
    )

    return {
        "sections": sections,
        "validation": validation,
    }


def extract_business_info(scraped_text: str, url: str = "") -> dict:
    """
    Uses AI to extract business information, brand attributes, and voice DNA from scraped text.
    
    Args:
        scraped_text (str): The text content from the webpage.
        url (str): The URL of the webpage (optional, for context).
        
    Returns:
        dict: Contains business_name, industry, key_customers, key_offer, brand_keywords, 
              niche_keywords, voice_tone_and_style, content_goals_ai, sample_posts, voice_dna,
              required_sections, validation, and target_audience fields.
              Returns None/empty values if extraction fails or AI is unavailable.
    """
    try:
        from services.ai_service import get_generative_model
        
        model = get_generative_model()
        if not model:
            logger.warning("AI service not available for business info extraction")
            base = {
                "business_name": None,
                "industry": None,
                "key_customers": None,
                "key_offer": None,
                "brand_keywords": [],
                "niche_keywords": [],
                "voice_dna": {}
            }
            required = _build_required_sections(scraped_text, url, base)
            base["required_sections"] = required["sections"]
            base["validation"] = required["validation"]
            base["target_audience"] = base["required_sections"]["target_audience"]["values"]
            return base
        
        # Limit text length for AI processing
        text_sample = scraped_text[:3000] if len(scraped_text) > 3000 else scraped_text
        
        # Format industry categories as properly quoted strings
        industries_list = ', '.join(json.dumps(cat) for cat in INDUSTRY_CATEGORIES)
        
        prompt = f"""Analyze the following website content and extract business information. Return ONLY a JSON object with these exact keys:

- business_name: The company/business name (string, or null if not found)
- industry: The business industry category - pick ONE that best matches from this list: {industries_list} (string, or null if not clear)
- key_customers: A brief description of the target audience/customers in 1-2 sentences (string, or null if not found)
- key_offer: The main value proposition, hook, or unique offer that this business promotes (e.g., "Free consultation", "30-day money-back guarantee", "Same-day delivery"). This should be their primary call-to-action or compelling offer, NOT truncated. Extract the complete offer text. (string, or null if not found)
- brand_keywords: A list of 3-5 key brand descriptors or values that represent this business (e.g., ["sustainable", "premium", "innovative"]) (array of strings)
- niche_keywords: A list of 3-5 niche-specific terms or specializations for this business (e.g., ["organic coffee", "artisan roasted", "fair trade"]) (array of strings)
- voice_tone_and_style: Analyze the writing style (formal, playful, authoritative, etc.) and provide 2-3 sentences describing the brand voice guidelines (string).
- content_goals: Infer 3-5 high-level content goals based on the site's calls to action (e.g., "Educate customers on X", "Drive sales for Y", "Build community") (array of strings).
- sample_posts: Generate 3 solid, high-quality sample social media posts (caption only) that perfectly fit this brand's voice and industry. (array of strings).
- voice_dna: Extract granular "Voice DNA" attributes from the content. This should be a JSON object with the following keys:
  - voice_rhythm: Describe the sentence length and pacing (e.g., "short and punchy", "long and flowing", "mixed cadence") (string)
  - emoji_style: Describe emoji usage patterns (e.g., "minimal", "heaps of ✨", "only at end", "scattered throughout", "none") (string)
  - forbidden_words: List words or phrases this brand avoids (e.g., ["jargon", "corporate speak", "buzzwords"]) (array of strings)
  - signature_signoffs: Common ways they end messages or posts (e.g., ["Cheers,", "Best,", "Stay awesome!"]) (array of strings)
  - sentence_structure: Notable sentence patterns or structures (e.g., "starts with verbs", "uses questions", "declarative statements") (string)

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
            "key_customers": extracted_data.get("key_customers") or None,
            "key_offer": extracted_data.get("key_offer") or None,
            "brand_keywords": extracted_data.get("brand_keywords") or [],
            "niche_keywords": extracted_data.get("niche_keywords") or [],
            "voice_tone_and_style": extracted_data.get("voice_tone_and_style") or None,
            "content_goals_ai": extracted_data.get("content_goals") or [],
            "sample_posts": extracted_data.get("sample_posts") or [],
            "voice_dna": extracted_data.get("voice_dna") or {}
        }

        required = _build_required_sections(scraped_text, url, result)
        result["required_sections"] = required["sections"]
        result["validation"] = required["validation"]
        # Add target audience list for downstream consumers
        result["target_audience"] = result["required_sections"]["target_audience"]["values"]
        
        logger.debug("Successfully extracted business info from scraped text")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        fallback = {
            "business_name": None,
            "industry": None,
            "key_customers": None,
            "key_offer": None,
            "brand_keywords": [],
            "niche_keywords": [],
            "voice_dna": {}
        }
        required = _build_required_sections(scraped_text, url, fallback)
        fallback["required_sections"] = required["sections"]
        fallback["validation"] = required["validation"]
        fallback["target_audience"] = fallback["required_sections"]["target_audience"]["values"]
        return fallback
    except Exception as e:
        logger.error(f"Failed to extract business info: {e}")
        fallback = {
            "business_name": None,
            "industry": None,
            "key_customers": None,
            "key_offer": None,
            "brand_keywords": [],
            "niche_keywords": [],
            "voice_dna": {}
        }
        required = _build_required_sections(scraped_text, url, fallback)
        fallback["required_sections"] = required["sections"]
        fallback["validation"] = required["validation"]
        fallback["target_audience"] = fallback["required_sections"]["target_audience"]["values"]
        return fallback
