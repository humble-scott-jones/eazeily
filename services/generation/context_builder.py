"""Context builder - merges workspace, profile, template, and request data.

Implements deterministic merge order:
  request > template > profile defaults > workspace defaults
"""

import json
from typing import Any, Dict, Optional, List
from .output_schemas import GenerationContext, WorkspaceContext, VoiceStyleGuide, BrandKitV1


def merge_contexts(
    workspace: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None,
    template: Optional[Dict[str, Any]] = None,
    request: Optional[Dict[str, Any]] = None,
    voice_guide: Optional[VoiceStyleGuide] = None,
    brand_kit: Optional[BrandKitV1] = None
) -> GenerationContext:
    """Merge multiple context sources with deterministic precedence.
    
    Merge order (highest to lowest priority):
    1. request - this specific generation request
    2. template - saved template if selected
    3. profile - user wizard settings
    4. workspace - account defaults
    
    Args:
        workspace: Workspace settings (company, industry, default tone/platforms)
        profile: User profile/wizard tuning (tone, creativity, platforms)
        template: Saved template (pre-configured settings)
        request: This request's toggles/parameters
        voice_guide: Derived voice style guide from samples
        brand_kit: Brand Kit v1 data (services, audience, proof, etc.)
        
    Returns:
        GenerationContext with merged settings
    """
    # Extract and evaluate brand_kit
    brand_kit_tier = None
    if brand_kit:
        brand_kit_tier = evaluate_brand_kit_tier(brand_kit)
    
    # Start with workspace defaults
    workspace_ctx = WorkspaceContext(
        company_name=workspace.get('company_name', '') if workspace else '',
        industry=workspace.get('industry', 'business') if workspace else 'business',
        default_tone=workspace.get('default_tone', 'professional') if workspace else 'professional',
        platforms=workspace.get('platforms', []) if workspace else [],
        offerings=workspace.get('offerings') if workspace else None,
        audience=workspace.get('audience') if workspace else None,
        compliance_notes=workspace.get('compliance_notes') if workspace else None,
        brand_kit=brand_kit,
        brand_kit_tier=brand_kit_tier
    )
    
    # Merge order: start with workspace, then layer profile, template, request
    merged: Dict[str, Any] = {}
    
    # Layer 1: Workspace
    if workspace:
        merged.update({
            'tone': workspace.get('default_tone'),
            'platforms': workspace.get('platforms'),
            'industry': workspace.get('industry'),
        })
    
    # Layer 2: Profile
    if profile:
        if profile.get('tone'):
            merged['tone'] = profile['tone']
        if profile.get('platforms'):
            merged['platforms'] = profile['platforms']
        if profile.get('creativity'):
            merged['creativity'] = profile['creativity']
        if profile.get('intensity'):
            merged['intensity'] = profile['intensity']
    
    # Layer 3: Template
    if template:
        if template.get('tone'):
            merged['tone'] = template['tone']
        if template.get('platforms'):
            merged['platforms'] = template['platforms']
        if template.get('goals'):
            merged['goals'] = template['goals']
        if template.get('keywords'):
            merged['keywords'] = template['keywords']
    
    # Layer 4: Request (highest priority)
    if request:
        # Request params override everything
        if request.get('tone'):
            merged['tone'] = request['tone']
        if request.get('platforms'):
            merged['platforms'] = request['platforms']
        if 'session_length' in request:
            merged['session_length'] = request['session_length']
        if 'goals' in request:
            merged['goals'] = request['goals']
        if 'keywords' in request:
            merged['keywords'] = request['keywords']
        if 'reel_options' in request:
            merged['reel_options'] = request['reel_options']
        if 'image_tailor' in request:
            merged['image_tailor'] = request['image_tailor']
        if 'use_brand_voice' in request:
            merged['use_brand_voice'] = request['use_brand_voice']
        
        # Chip selections - request overrides profile
        if 'selected_audience_ids' in request:
            merged['selected_audience_ids'] = request['selected_audience_ids']
        elif profile and 'selected_audience_ids' in profile:
            merged['selected_audience_ids'] = profile['selected_audience_ids']
        
        if 'selected_offer_ids' in request:
            merged['selected_offer_ids'] = request['selected_offer_ids']
        elif profile and 'selected_offer_ids' in profile:
            merged['selected_offer_ids'] = profile['selected_offer_ids']
        
        if 'selected_proof_ids' in request:
            merged['selected_proof_ids'] = request['selected_proof_ids']
        elif profile and 'selected_proof_ids' in profile:
            merged['selected_proof_ids'] = profile['selected_proof_ids']
        
        if 'selected_focus_topic_ids' in request:
            merged['selected_focus_topic_ids'] = request['selected_focus_topic_ids']
        elif profile and 'selected_focus_topic_ids' in profile:
            merged['selected_focus_topic_ids'] = profile['selected_focus_topic_ids']
        
        if 'selected_cta_intent_id' in request:
            merged['selected_cta_intent_id'] = request['selected_cta_intent_id']
        elif profile and 'selected_cta_intent_id' in profile:
            merged['selected_cta_intent_id'] = profile['selected_cta_intent_id']
        
        if 'custom_chips' in request:
            merged['custom_chips'] = request['custom_chips']
        elif profile and 'custom_chips' in profile:
            merged['custom_chips'] = profile['custom_chips']
        
        # Copy any other request-specific params
        for key in request:
            if key not in merged:
                merged[key] = request[key]
    else:
        # No request, use profile chips if available
        if profile:
            if 'selected_audience_ids' in profile:
                merged['selected_audience_ids'] = profile['selected_audience_ids']
            if 'selected_offer_ids' in profile:
                merged['selected_offer_ids'] = profile['selected_offer_ids']
            if 'selected_proof_ids' in profile:
                merged['selected_proof_ids'] = profile['selected_proof_ids']
            if 'selected_focus_topic_ids' in profile:
                merged['selected_focus_topic_ids'] = profile['selected_focus_topic_ids']
            if 'selected_cta_intent_id' in profile:
                merged['selected_cta_intent_id'] = profile['selected_cta_intent_id']
            if 'custom_chips' in profile:
                merged['custom_chips'] = profile['custom_chips']
    
    # Build final context
    context = GenerationContext(
        workspace=workspace_ctx,
        voice_guide=voice_guide,
        template=template,
        request=merged
    )
    
    return context


def validate_required_fields(context: GenerationContext, required: List[str]) -> Dict[str, str]:
    """Validate that required fields are present in merged context.
    
    Args:
        context: Merged generation context
        required: List of required field names
        
    Returns:
        Dict mapping field names to error messages (empty if valid)
    """
    errors: Dict[str, str] = {}
    request_data = context.get('request', {})
    
    for field in required:
        # Check in request first, then workspace
        value = request_data.get(field)
        if not value and context.get('workspace'):
            value = context['workspace'].get(field)
        
        if not value:
            errors[field] = f"Required field '{field}' is missing"
    
    return errors


def extract_merged_params(context: GenerationContext) -> Dict[str, Any]:
    """Extract merged parameters from context for generation.
    
    Returns a flat dict with final values for all parameters.
    """
    request_data = context.get('request', {})
    workspace_data = context.get('workspace', {})
    
    return {
        'tone': request_data.get('tone') or workspace_data.get('default_tone', 'professional'),
        'platforms': request_data.get('platforms') or workspace_data.get('platforms', []),
        'industry': request_data.get('industry') or workspace_data.get('industry', 'business'),
        'company_name': workspace_data.get('company_name', ''),
        'session_length': request_data.get('session_length', 7),
        'goals': request_data.get('goals', []),
        'keywords': request_data.get('keywords', []),
        'creativity': request_data.get('creativity'),
        'intensity': request_data.get('intensity'),
        'reel_options': request_data.get('reel_options', {}),
        'use_brand_voice': request_data.get('use_brand_voice', False),
        'variant_types': request_data.get('variant_types', []),
    }


def get_workspace_summary(context: GenerationContext) -> str:
    """Generate a compact text summary of workspace context for prompts."""
    workspace = context.get('workspace', {})
    parts = []
    
    if company_name := workspace.get('company_name'):
        parts.append(f"Company: {company_name}")
    
    if industry := workspace.get('industry'):
        parts.append(f"Industry: {industry}")
    
    if offerings := workspace.get('offerings'):
        parts.append(f"Offerings: {offerings}")
    
    if audience := workspace.get('audience'):
        parts.append(f"Audience: {audience}")
    
    return ". ".join(parts) + "." if parts else ""


def evaluate_brand_kit_tier(brand_kit: BrandKitV1) -> str:
    """Evaluate Brand Kit completeness tier.
    
    Tiers:
    - "minimum": At least 1 service
    - "stronger": Services + audience (role/pain/outcome) 
    - "best": Services + audience + (proof or differentiators)
    
    Args:
        brand_kit: Brand Kit data
        
    Returns:
        Tier string: "minimum" | "stronger" | "best"
    """
    has_services = bool(brand_kit.get('services'))
    has_audience = bool(
        brand_kit.get('audience_role') or 
        brand_kit.get('audience_pain') or 
        brand_kit.get('audience_outcome')
    )
    has_proof_or_diff = bool(
        brand_kit.get('proof') or 
        brand_kit.get('differentiators')
    )
    
    if has_services and has_audience and has_proof_or_diff:
        return "best"
    elif has_services and has_audience:
        return "stronger"
    elif has_services:
        return "minimum"
    else:
        return "incomplete"


def extract_brand_kit_from_user_data(user_data: Dict[str, Any]) -> Optional[BrandKitV1]:
    """Extract Brand Kit v1 from user/profile data.
    
    Args:
        user_data: User or profile dict that may contain brand_kit fields
        
    Returns:
        BrandKitV1 dict or None if no brand kit data found
    """
    # Check if brand_kit is already structured
    if 'brand_kit' in user_data and isinstance(user_data['brand_kit'], dict):
        return user_data['brand_kit']
    
    # Otherwise, construct from individual fields (backward compatibility)
    brand_kit: BrandKitV1 = {}
    
    # Map fields - these might be stored as JSON strings or direct fields
    if 'services' in user_data:
        services = user_data['services']
        if isinstance(services, str):
            try:
                services = json.loads(services)
            except (json.JSONDecodeError, ValueError):
                services = [s.strip() for s in services.split(',') if s.strip()]
        if services:
            brand_kit['services'] = services
    
    if 'audience_role' in user_data and user_data['audience_role']:
        brand_kit['audience_role'] = user_data['audience_role']
    
    if 'audience_pain' in user_data and user_data['audience_pain']:
        brand_kit['audience_pain'] = user_data['audience_pain']
    
    if 'audience_outcome' in user_data and user_data['audience_outcome']:
        brand_kit['audience_outcome'] = user_data['audience_outcome']
    
    if 'audience_objection' in user_data and user_data['audience_objection']:
        brand_kit['audience_objection'] = user_data['audience_objection']
    
    if 'differentiators' in user_data:
        differentiators = user_data['differentiators']
        if isinstance(differentiators, str):
            try:
                differentiators = json.loads(differentiators)
            except (json.JSONDecodeError, ValueError):
                differentiators = [d.strip() for d in differentiators.split(',') if d.strip()]
        if differentiators:
            brand_kit['differentiators'] = differentiators
    
    if 'proof' in user_data:
        proof = user_data['proof']
        if isinstance(proof, str):
            try:
                proof = json.loads(proof)
            except (json.JSONDecodeError, ValueError):
                proof = [p.strip() for p in proof.split(',') if p.strip()]
        if proof:
            brand_kit['proof'] = proof
    
    if 'email_signature' in user_data and user_data['email_signature']:
        brand_kit['email_signature'] = user_data['email_signature']
    
    if 'quote_terms' in user_data and user_data['quote_terms']:
        brand_kit['quote_terms'] = user_data['quote_terms']
    
    return brand_kit if brand_kit else None


def extract_chip_selections(
    request: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None,
    brand_kit: Optional[BrandKitV1] = None,
    industry_id: Optional[str] = None
) -> Dict[str, List[str]]:
    """Extract chip selections from various sources with precedence.
    
    Precedence (highest to lowest):
    1. request - current request chip selections
    2. profile - saved profile chip selections
    3. brand_kit - chips derived from brand kit data
    4. industry defaults - loaded from industry packs (handled separately)
    
    Args:
        request: Current request data
        profile: User profile data
        brand_kit: Brand Kit data
        industry_id: Industry ID for loading defaults
        
    Returns:
        Dict with chip categories: {
            'audience': [chip_id...],
            'offers': [chip_id...],
            'proof': [chip_id...],
            'focus_topics': [chip_id...]
        }
    """
    chips: Dict[str, List[str]] = {
        'audience': [],
        'offers': [],
        'proof': [],
        'focus_topics': []
    }
    
    # Layer 1: Extract from brand kit (lowest priority among sources)
    if brand_kit:
        # Map brand kit services to offer chips
        if services := brand_kit.get('services'):
            chips['offers'].extend(services[:5])  # Limit to 5
        
        # Map proof to proof chips
        if proof := brand_kit.get('proof'):
            chips['proof'].extend(proof[:3])  # Limit to 3
        
        # Map audience data to audience chips
        audience_parts = []
        if role := brand_kit.get('audience_role'):
            audience_parts.append(role)
        if pain := brand_kit.get('audience_pain'):
            audience_parts.append(pain)
        if outcome := brand_kit.get('audience_outcome'):
            audience_parts.append(outcome)
        
        if audience_parts:
            # Use first 2 audience signals
            chips['audience'].extend(audience_parts[:2])
    
    # Layer 2: Profile saved selections (override brand kit)
    if profile:
        if selected_audience := profile.get('selected_audience_ids'):
            chips['audience'] = list(selected_audience)  # Replace brand kit
        
        if selected_offers := profile.get('selected_offer_ids'):
            chips['offers'] = list(selected_offers)  # Replace brand kit
        
        if selected_proof := profile.get('selected_proof_ids'):
            chips['proof'] = list(selected_proof)  # Replace brand kit
        
        if selected_topics := profile.get('selected_focus_topic_ids'):
            chips['focus_topics'] = list(selected_topics)
    
    # Layer 3: Request selections (highest priority - override all)
    if request:
        if selected_audience := request.get('selected_audience_ids'):
            chips['audience'] = list(selected_audience)
        
        if selected_offers := request.get('selected_offer_ids'):
            chips['offers'] = list(selected_offers)
        
        if selected_proof := request.get('selected_proof_ids'):
            chips['proof'] = list(selected_proof)
        
        if selected_topics := request.get('selected_focus_topic_ids'):
            chips['focus_topics'] = list(selected_topics)
    
    return chips


def format_brand_kit_bullets(brand_kit: BrandKitV1) -> Dict[str, str]:
    """Format Brand Kit data as bullet-point text sections.
    
    Args:
        brand_kit: Brand Kit data
        
    Returns:
        Dict with formatted sections: business_summary, services_bullets, 
        audience_bullets, proof_bullets, differentiators_bullets
    """
    sections = {}
    
    # Business summary (compact)
    summary_parts = []
    if services := brand_kit.get('services'):
        summary_parts.append(f"Services: {', '.join(services[:3])}")
    if role := brand_kit.get('audience_role'):
        summary_parts.append(f"For: {role}")
    sections['business_summary'] = ". ".join(summary_parts) + "." if summary_parts else ""
    
    # Services bullets
    if services := brand_kit.get('services'):
        sections['services_bullets'] = "\n".join([f"• {s}" for s in services])
    else:
        sections['services_bullets'] = ""
    
    # Audience bullets (role/pain/outcome/objection)
    audience_bullets = []
    if role := brand_kit.get('audience_role'):
        audience_bullets.append(f"• Who: {role}")
    if pain := brand_kit.get('audience_pain'):
        audience_bullets.append(f"• Pain: {pain}")
    if outcome := brand_kit.get('audience_outcome'):
        audience_bullets.append(f"• Outcome: {outcome}")
    if objection := brand_kit.get('audience_objection'):
        audience_bullets.append(f"• Objection: {objection}")
    sections['audience_bullets'] = "\n".join(audience_bullets)
    
    # Proof bullets
    if proof := brand_kit.get('proof'):
        sections['proof_bullets'] = "\n".join([f"• {p}" for p in proof])
    else:
        sections['proof_bullets'] = ""
    
    # Differentiators bullets
    if diff := brand_kit.get('differentiators'):
        sections['differentiators_bullets'] = "\n".join([f"• {d}" for d in diff])
    else:
        sections['differentiators_bullets'] = ""
    
    return sections
