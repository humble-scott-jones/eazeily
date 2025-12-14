"""Context builder - merges workspace, profile, template, and request data.

Implements deterministic merge order:
  request > template > profile defaults > workspace defaults
"""

from typing import Any, Dict, Optional, List
from .output_schemas import GenerationContext, WorkspaceContext, VoiceStyleGuide


def merge_contexts(
    workspace: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None,
    template: Optional[Dict[str, Any]] = None,
    request: Optional[Dict[str, Any]] = None,
    voice_guide: Optional[VoiceStyleGuide] = None
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
        
    Returns:
        GenerationContext with merged settings
    """
    # Start with workspace defaults
    workspace_ctx = WorkspaceContext(
        company_name=workspace.get('company_name', '') if workspace else '',
        industry=workspace.get('industry', 'business') if workspace else 'business',
        default_tone=workspace.get('default_tone', 'professional') if workspace else 'professional',
        platforms=workspace.get('platforms', []) if workspace else [],
        offerings=workspace.get('offerings') if workspace else None,
        audience=workspace.get('audience') if workspace else None,
        compliance_notes=workspace.get('compliance_notes') if workspace else None,
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
        # Copy any other request-specific params
        for key in request:
            if key not in merged:
                merged[key] = request[key]
    
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
