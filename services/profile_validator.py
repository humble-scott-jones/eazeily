"""Profile completeness validation service.

This module provides utilities for validating user profile completeness
before content generation.
"""

from typing import Tuple, List


def get_profile_completeness(profile) -> Tuple[bool, List[str], int]:
    """
    Check profile completeness and return missing fields.
    
    Args:
        profile: VoiceProfile instance to check
    
    Returns:
        tuple: (is_complete: bool, missing_fields: list, completeness_percent: int)
    """
    REQUIRED_FIELDS = {
        'business_name': 'Business Name',
        'industry': 'Industry', 
        'brand_voice': 'Brand Voice',
        'target_audience': 'Target Audience',
        'key_offer': 'Key Offer',
    }
    
    OPTIONAL_FIELDS = {
        'writing_samples': 'Writing Samples',  # Check via get_writing_samples()
        'brand_keywords': 'Brand Keywords',    # Check via get_brand_keywords()
        'goals': 'Goals',                      # Check via get_goals()
    }
    
    if not profile:
        # If no profile at all, all fields are missing
        all_missing = list(REQUIRED_FIELDS.values()) + list(OPTIONAL_FIELDS.values())
        return False, all_missing, 0
    
    missing = []
    filled = 0
    total = len(REQUIRED_FIELDS) + len(OPTIONAL_FIELDS)
    
    # Check required fields
    for field, label in REQUIRED_FIELDS.items():
        value = getattr(profile, field, None)
        if value and str(value).strip():
            filled += 1
        else:
            missing.append(label)
    
    # Check writing samples separately (stored as JSON)
    samples = profile.get_writing_samples() if hasattr(profile, 'get_writing_samples') else []
    if samples and len(samples) > 0:
        filled += 1
    else:
        missing.append('Writing Samples')
    
    # Check brand keywords (stored as JSON)
    keywords = profile.get_brand_keywords() if hasattr(profile, 'get_brand_keywords') else []
    if keywords and len(keywords) > 0:
        filled += 1
    else:
        missing.append('Brand Keywords')
    
    # Check goals (stored as JSON)
    goals = profile.get_goals() if hasattr(profile, 'get_goals') else []
    if goals and len(goals) > 0:
        filled += 1
    else:
        missing.append('Goals')
    
    completeness = int((filled / total) * 100)
    is_complete = len([f for f in missing if f in REQUIRED_FIELDS.values()]) == 0
    
    return is_complete, missing, completeness


def format_missing_fields_message(missing_fields: List[str]) -> str:
    """
    Format missing fields into a user-friendly message.
    
    Args:
        missing_fields: List of missing field labels
    
    Returns:
        Formatted message string
    """
    if not missing_fields:
        return ""
    
    if len(missing_fields) == 1:
        return missing_fields[0]
    elif len(missing_fields) == 2:
        return f"{missing_fields[0]} and {missing_fields[1]}"
    else:
        return f"{', '.join(missing_fields[:-1])}, and {missing_fields[-1]}"
