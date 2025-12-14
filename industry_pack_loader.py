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
        "prompt_integration_hooks",
        "good_defaults"
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
    
    # Validate good_defaults structure
    if "good_defaults" in pack_data:
        gd = pack_data["good_defaults"]
        
        # Validate audience
        if "audience" not in gd:
            errors.append("good_defaults missing audience")
        else:
            aud = gd["audience"]
            if "who" not in aud:
                errors.append("good_defaults.audience missing who")
            if "pain_points" not in aud or len(aud.get("pain_points", [])) < 3:
                errors.append("good_defaults.audience.pain_points must have at least 3 items")
            if "desired_outcomes" not in aud or len(aud.get("desired_outcomes", [])) < 3:
                errors.append("good_defaults.audience.desired_outcomes must have at least 3 items")
        
        # Validate offers
        if "offers" not in gd:
            errors.append("good_defaults missing offers")
        else:
            off = gd["offers"]
            if "common_services" not in off or len(off.get("common_services", [])) < 5:
                errors.append("good_defaults.offers.common_services must have at least 5 items")
            if "ctas" not in off or len(off.get("ctas", [])) < 4:
                errors.append("good_defaults.offers.ctas must have at least 4 items")
        
        # Validate proof
        if "proof" not in gd:
            errors.append("good_defaults missing proof")
        else:
            if "common_proof_points" not in gd["proof"] or len(gd["proof"].get("common_proof_points", [])) < 4:
                errors.append("good_defaults.proof.common_proof_points must have at least 4 items")
        
        # Validate content_angles
        if "content_angles" not in gd:
            errors.append("good_defaults missing content_angles")
        elif len(gd.get("content_angles", [])) < 6:
            errors.append("good_defaults.content_angles must have at least 6 items")
        
        # Validate chip_presets
        if "chip_presets" not in gd:
            errors.append("good_defaults missing chip_presets")
        else:
            cp = gd["chip_presets"]
            if "focus_topics" not in cp or len(cp.get("focus_topics", [])) < 8:
                errors.append("good_defaults.chip_presets.focus_topics must have at least 8 items")
            if "audience_chips" not in cp or len(cp.get("audience_chips", [])) < 6:
                errors.append("good_defaults.chip_presets.audience_chips must have at least 6 items")
            if "offer_chips" not in cp or len(cp.get("offer_chips", [])) < 6:
                errors.append("good_defaults.chip_presets.offer_chips must have at least 6 items")
            if "proof_chips" not in cp or len(cp.get("proof_chips", [])) < 6:
                errors.append("good_defaults.chip_presets.proof_chips must have at least 6 items")
    
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


def get_industry_pack(industry_id: str) -> Dict[str, Any]:
    """Get an industry pack by ID with fallback to 'general'.
    
    This is the primary helper function to use for getting industry packs.
    If the requested industry pack doesn't exist, it falls back to the 
    'general' pack which provides safe defaults.
    
    Args:
        industry_id: The industry pack identifier (e.g., 'salon', 'dentist')
        
    Returns:
        Dict containing the industry pack data. Returns 'general' pack if
        the requested pack is not found. Never returns None.
    """
    pack = load_industry_pack(industry_id)
    if pack:
        return pack
    
    # Fallback to general pack
    logger.info(f"Industry pack '{industry_id}' not found, falling back to 'general'")
    general_pack = load_industry_pack('general')
    if general_pack:
        return general_pack
    
    # If even general doesn't exist, log error and return a minimal pack
    logger.error("General industry pack not found! Returning minimal fallback")
    return {
        "id": "general",
        "display_name": "General Business",
        "icon": "✨",
        "primary_customer_goal": "leads",
        "version": "1.0.0"
    }


def get_good_defaults(industry_id: str) -> Dict[str, Any]:
    """Get GOOD defaults for an industry (chip presets, audience, offers, etc).
    
    Args:
        industry_id: The industry pack identifier (must be a string)
        
    Returns:
        Dict containing good_defaults, or empty dict if not found
        
    Raises:
        TypeError: If industry_id is not a string
    """
    if not isinstance(industry_id, str):
        raise TypeError(f"industry_id must be a string, got {type(industry_id).__name__}")
    
    pack = get_industry_pack(industry_id)
    return pack.get("good_defaults", {})
