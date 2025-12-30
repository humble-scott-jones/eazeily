"""Minimal generation service package shim.

This package provides a tiny, resilient GenerationService and a no-op
OpenAI adapter so the app can start in environments where the full
generation stack isn't installed. Later we can replace these with the
full implementations.
"""
from .generation_service import GenerationService

__all__ = ["GenerationService"]
