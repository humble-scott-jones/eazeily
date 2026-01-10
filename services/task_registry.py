"""Central registry for generation task types and their prompt templates.

This keeps task definitions declarative so the API handler and VoiceEngine can
validate and render prompts without scattering constants across files.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class TaskConfig:
    """Configuration for a single generation task type."""

    key: str
    role: str
    prompt_template: str
    require_platform: bool = False


# Declarative registry of supported task types.
_TASK_REGISTRY: Dict[str, TaskConfig] = {
    "post": TaskConfig(
        key="post",
        role="Social Media Manager",
        require_platform=True,
        prompt_template=(
            "Write an engaging {platform} post about {topic}. "
            "Make it platform-appropriate, shareable, and include a call-to-action."
        ),
    ),
    "ad": TaskConfig(
        key="ad",
        role="Advertising Copywriter",
        prompt_template=(
            "Write a high-converting Facebook/Instagram ad for {topic}. "
            "Focus on the hook, value proposition, and clear CTA with the offer: {key_offer}. "
            "Keep it punchy and scroll-stopping."
        ),
    ),
    "email": TaskConfig(
        key="email",
        role="Email Marketing Specialist",
        prompt_template=(
            "Write a warm, personalized outreach email about {topic}. "
            "Include an attention-grabbing subject line. Make it conversational and relationship-first."
        ),
    ),
    "review": TaskConfig(
        key="review",
        role="Customer Service Manager",
        prompt_template=(
            "Draft a professional, empathetic response to this customer review: {topic}. "
            "Show appreciation, address concerns, and reinforce brand values."
        ),
    ),
    "proposal": TaskConfig(
        key="proposal",
        role="Business Development Manager",
        prompt_template=(
            "Write a professional business proposal for {topic}. "
            "Include: project overview, deliverables, timeline, pricing structure, and value proposition."
        ),
    ),
    "newsletter": TaskConfig(
        key="newsletter",
        role="Content Marketing Lead",
        prompt_template=(
            "Write an engaging newsletter section about {topic}. "
            "Include a catchy headline, valuable content, and a clear next step for readers."
        ),
    ),
    "blog": TaskConfig(
        key="blog",
        role="Content Writer and SEO Specialist",
        prompt_template=(
            "Write an informative, SEO-friendly blog post about {topic}. "
            "Include: engaging introduction, key points with subheadings, actionable takeaways, and a conclusion with CTA."
        ),
    ),
    "script": TaskConfig(
        key="script",
        role="Video Content Creator",
        prompt_template=(
            "Write a video script for {topic}. "
            "Include: hook (first 3 seconds), main content with visual cues, and strong CTA. "
            "Format with timestamps and shot descriptions."
        ),
    ),
    "caption": TaskConfig(
        key="caption",
        role="Social Media Content Specialist",
        prompt_template=(
            "Write a compelling social media caption for this image: {topic}. "
            "Capture attention, add context, and include relevant hashtags."
        ),
    ),
}


def get_task_config(task_type: str) -> Optional[TaskConfig]:
    return _TASK_REGISTRY.get((task_type or "").strip())


def list_task_types() -> list[str]:
    return list(_TASK_REGISTRY.keys())


def is_valid_task(task_type: str) -> bool:
    return task_type in _TASK_REGISTRY
