from __future__ import annotations
from typing import Any, Dict, List, Optional

DEFAULT_WORKSPACE = {
    "company_name": "",
    "industry": "business",
    "default_tone": "professional",
    "platforms": ["instagram"],
}

DEFAULT_REQUEST = {
    "tone": "professional",
    "session_length": 7,
    "platforms": ["instagram"],
}


def _merge_dict(base: Dict[str, Any], override: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out = dict(base or {})
    if override:
        out.update({k: v for k, v in override.items() if v is not None})
    return out


def merge_contexts(
    *,
    workspace: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None,
    template: Optional[Dict[str, Any]] = None,
    request: Optional[Dict[str, Any]] = None,
    brand_kit: Optional[Dict[str, Any]] = None,
    voice_guide: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ws = _merge_dict(DEFAULT_WORKSPACE, workspace)
    prof = profile or {}
    tpl = template or {}
    req = _merge_dict(_merge_dict(prof, tpl), request or {})
    req = _merge_dict(DEFAULT_REQUEST, req)

    # chip selections
    for key in ["selected_audience_ids", "selected_offer_ids", "selected_proof_ids"]:
        if key not in req and key in prof:
            req[key] = prof[key]
        if key in tpl:
            req[key] = tpl[key]
        if request and key in request:
            req[key] = request[key]

    # custom chips passthrough
    if prof.get("custom_chips") and "custom_chips" not in req:
        req["custom_chips"] = prof.get("custom_chips")

    ctx = {
        "workspace": ws,
        "profile": prof,
        "template": tpl,
        "request": req,
    }
    if brand_kit:
        ctx["workspace"]["brand_kit"] = brand_kit
        ctx["workspace"]["brand_kit_tier"] = evaluate_brand_kit_tier(brand_kit)
    else:
        ctx["workspace"].setdefault("brand_kit", None)
        ctx["workspace"].setdefault("brand_kit_tier", None)

    if voice_guide:
        ctx["voice_guide"] = voice_guide
    return ctx


def validate_required_fields(context: Dict[str, Any], required: List[str]) -> List[str]:
    errors: List[str] = []
    merged = extract_merged_params(context)
    for field in required:
        if not merged.get(field):
            errors.append(field)
    return errors


def extract_merged_params(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    context = context or merge_contexts()
    workspace = context.get("workspace", {})
    request = context.get("request", {})
    merged = _merge_dict(workspace, request)
    merged.setdefault("tone", DEFAULT_REQUEST["tone"])
    merged.setdefault("session_length", DEFAULT_REQUEST["session_length"])
    merged.setdefault("platforms", DEFAULT_REQUEST["platforms"])
    merged.setdefault("industry", DEFAULT_WORKSPACE["industry"])
    return merged


def get_workspace_summary(context: Dict[str, Any]) -> str:
    ws = (context or {}).get("workspace", {})
    parts = []
    for key in ["company_name", "industry", "offerings", "audience"]:
        value = ws.get(key)
        if value:
            parts.append(str(value))
    return "; ".join(parts)


def extract_chip_selections(
    *, profile: Optional[Dict[str, Any]] = None, brand_kit: Optional[Dict[str, Any]] = None
) -> Dict[str, List[str]]:
    profile = profile or {}
    chips = {
        "audience": list(profile.get("selected_audience_ids", []) or []),
        "offers": list(profile.get("selected_offer_ids", []) or []),
        "proof": list(profile.get("selected_proof_ids", []) or []),
    }
    if brand_kit:
        if brand_kit.get("services"):
            chips["offers"].extend(brand_kit["services"])
        if brand_kit.get("proof"):
            chips["proof"].extend(brand_kit["proof"])
    return chips


def extract_brand_kit_from_user_data(user_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not user_data:
        return None
    if isinstance(user_data.get("brand_kit"), dict):
        return user_data["brand_kit"]
    # backward compatibility: accept csv/ json strings
    brand_kit: Dict[str, Any] = {}
    for key in ["services", "audience_role", "audience_pain", "audience_outcome", "audience_objection", "differentiators", "proof"]:
        if key in user_data:
            raw = user_data[key]
            if isinstance(raw, str):
                if raw.strip().startswith("["):
                    try:
                        import json
                        brand_kit[key] = json.loads(raw)
                    except Exception:
                        brand_kit[key] = [s.strip() for s in raw.split(",") if s.strip()]
                else:
                    brand_kit[key] = [s.strip() for s in raw.split(",") if s.strip()] if key in {"services", "differentiators", "proof"} else raw
            else:
                brand_kit[key] = raw
    return brand_kit or None


BRAND_KIT_TIERS = ["incomplete", "minimum", "stronger", "best"]


def evaluate_brand_kit_tier(brand_kit: Optional[Dict[str, Any]]) -> str:
    if not brand_kit:
        return "incomplete"
    services = bool(brand_kit.get("services"))
    role = bool(brand_kit.get("audience_role") or brand_kit.get("audience_outcome"))
    differentiators = bool(brand_kit.get("differentiators"))
    proof = bool(brand_kit.get("proof"))
    if services and role and (differentiators or proof):
        return "best"
    if services and role:
        return "stronger"
    if services:
        return "minimum"
    return "incomplete"


def format_brand_kit_bullets(brand_kit: Optional[Dict[str, Any]]) -> Dict[str, str]:
    brand_kit = brand_kit or {}
    def bullets(items: List[str], prefix: str = "• ") -> str:
        return "\n".join(f"{prefix}{item}" for item in items if item)

    services_bullets = bullets(list(brand_kit.get("services", [])))
    audience_parts = []
    if brand_kit.get("audience_role"):
        audience_parts.append(f"• Who: {brand_kit['audience_role']}")
    if brand_kit.get("audience_pain"):
        audience_parts.append(f"• Pain: {brand_kit['audience_pain']}")
    if brand_kit.get("audience_outcome"):
        audience_parts.append(f"• Outcome: {brand_kit['audience_outcome']}")
    if brand_kit.get("audience_objection"):
        audience_parts.append(f"• Objection: {brand_kit['audience_objection']}")

    proof_bullets = bullets(list(brand_kit.get("proof", [])))
    differentiators_bullets = bullets(list(brand_kit.get("differentiators", [])))

    business_summary_parts = []
    if brand_kit.get("services"):
        business_summary_parts.append(", ".join(brand_kit["services"]))
    if brand_kit.get("audience_role"):
        business_summary_parts.append(str(brand_kit["audience_role"]))
    business_summary = " - ".join(business_summary_parts)

    return {
        "business_summary": business_summary,
        "services_bullets": services_bullets,
        "audience_bullets": "\n".join(audience_parts),
        "proof_bullets": proof_bullets,
        "differentiators_bullets": differentiators_bullets,
    }
