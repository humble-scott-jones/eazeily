"""Industry Pack Loader - Loads and validates industry pack definitions."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Cache for loaded industry packs
_INDUSTRY_PACKS_CACHE: Dict[str, Dict[str, Any]] = {}
_SCHEMA_CACHE: Optional[Dict[str, Any]] = None


def get_industry_packs_dir() -> Path:
    """Get the directory containing industry packs."""
    return Path(__file__).parent / "industry_packs" / "v1"


def load_schema() -> Dict[str, Any]:
    """Load the industry pack JSON schema."""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is not None:
        return _SCHEMA_CACHE
    
    schema_path = get_industry_packs_dir() / "schema.json"
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            _SCHEMA_CACHE = json.load(f)
            return _SCHEMA_CACHE
    except Exception as e:
        logger.warning(f"Failed to load industry pack schema: {e}")
        return {}


def load_industry_pack(industry_id: str) -> Optional[Dict[str, Any]]:
    """Load an industry pack by ID.
    
    Args:
        industry_id: The industry pack identifier (e.g., 'salon', 'dentist')
        
    Returns:
        Dict containing the industry pack data, or None if not found
    """
    # Check cache first
    if industry_id in _INDUSTRY_PACKS_CACHE:
        return _INDUSTRY_PACKS_CACHE[industry_id]
    
    # Try to load from file
    pack_path = get_industry_packs_dir() / f"{industry_id}.json"
    if not pack_path.exists():
        logger.debug(f"Industry pack not found: {industry_id}")
        return None
    
    try:
        with open(pack_path, 'r', encoding='utf-8') as f:
            pack_data = json.load(f)
            _INDUSTRY_PACKS_CACHE[industry_id] = pack_data
            logger.debug(f"Loaded industry pack: {industry_id}")
            return pack_data
    except Exception as e:
        logger.error(f"Failed to load industry pack {industry_id}: {e}")
        return None


def get_available_industry_packs() -> list[str]:
    """Get list of available industry pack IDs."""
    packs_dir = get_industry_packs_dir()
    if not packs_dir.exists():
        return []
    
    packs = []
    for pack_file in packs_dir.glob("*.json"):
        if pack_file.stem != "schema":
            packs.append(pack_file.stem)
    
    return sorted(packs)


def validate_industry_pack(pack_data: Dict[str, Any]) -> list[str]:
    """Validate an industry pack against required fields.
    
    Args:
        pack_data: The industry pack data to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    required_fields = [
        "id",
        "display_name",
        "primary_customer_goal",
        "version",
        "business_profile_fields",
        "default_channel_strategy",
        "keyword_banks",
        "cta_library",
        "compliance_safety_rules",
        "content_templates",
        "example_outputs",
        "prompt_integration_hooks"
    ]
    
    for field in required_fields:
        if field not in pack_data:
            errors.append(f"Missing required field: {field}")
    
    # Validate nested structures
    if "keyword_banks" in pack_data:
        kb = pack_data["keyword_banks"]
        if "seed_keywords" not in kb:
            errors.append("keyword_banks missing seed_keywords")
        elif len(kb.get("seed_keywords", [])) < 10:
            errors.append("keyword_banks.seed_keywords must have at least 10 items")
        
        if "topic_clusters" not in kb:
            errors.append("keyword_banks missing topic_clusters")
    
    if "cta_library" in pack_data:
        cta = pack_data["cta_library"]
        for cta_type in ["booking_ctas", "inquiry_ctas", "review_referral_ctas", "offer_ctas"]:
            if cta_type not in cta:
                errors.append(f"cta_library missing {cta_type}")
            elif len(cta.get(cta_type, [])) < 3:
                errors.append(f"cta_library.{cta_type} must have at least 3 items")
    
    return errors


def get_industry_keywords(industry_id: str) -> list[str]:
    """Get seed keywords for an industry.
    
    Args:
        industry_id: The industry pack identifier
        
    Returns:
        List of seed keywords, or empty list if not found
    """
    pack = load_industry_pack(industry_id)
    if not pack:
        return []
    
    return pack.get("keyword_banks", {}).get("seed_keywords", [])


def get_industry_ctas(industry_id: str, cta_type: str = "booking_ctas") -> list[str]:
    """Get CTAs for an industry.
    
    Args:
        industry_id: The industry pack identifier
        cta_type: Type of CTA (booking_ctas, inquiry_ctas, review_referral_ctas, offer_ctas)
        
    Returns:
        List of CTAs, or empty list if not found
    """
    pack = load_industry_pack(industry_id)
    if not pack:
        return []
    
    return pack.get("cta_library", {}).get(cta_type, [])


def get_industry_compliance_rules(industry_id: str) -> Dict[str, Any]:
    """Get compliance and safety rules for an industry.
    
    Args:
        industry_id: The industry pack identifier
        
    Returns:
        Dict containing compliance rules, or empty dict if not found
    """
    pack = load_industry_pack(industry_id)
    if not pack:
        return {}
    
    return pack.get("compliance_safety_rules", {})


def get_industry_constraints(industry_id: str) -> Dict[str, list[str]]:
    """Get prompt constraints for an industry (do/don't lists).
    
    Args:
        industry_id: The industry pack identifier
        
    Returns:
        Dict with 'do' and 'dont' lists, or empty dict if not found
    """
    pack = load_industry_pack(industry_id)
    if not pack:
        return {"do": [], "dont": []}
    
    hooks = pack.get("prompt_integration_hooks", {})
    return hooks.get("default_do_dont_list", {"do": [], "dont": []})


def get_default_platforms(industry_id: str) -> list[str]:
    """Get default platforms for an industry.
    
    Args:
        industry_id: The industry pack identifier
        
    Returns:
        List of platform keys, or empty list if not found
    """
    pack = load_industry_pack(industry_id)
    if not pack:
        return []
    
    strategy = pack.get("default_channel_strategy", {})
    return strategy.get("default_platforms", [])


def get_topic_clusters(industry_id: str) -> list[Dict[str, Any]]:
    """Get topic clusters for an industry.
    
    Args:
        industry_id: The industry pack identifier
        
    Returns:
        List of topic cluster dicts, or empty list if not found
    """
    pack = load_industry_pack(industry_id)
    if not pack:
        return []
    
    kb = pack.get("keyword_banks", {})
    return kb.get("topic_clusters", [])
