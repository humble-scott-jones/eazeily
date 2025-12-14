"""
Preview template builder - loads and processes preview templates.

This module provides deterministic, offline-capable preview templates
for social, email, and quote channels without requiring OpenAI.
"""

import json
import os
import re
from typing import Dict, List, Any, Optional


class PreviewTemplateBuilder:
    """Builds preview content from templates with slot substitution."""
    
    def __init__(self, templates_dir: Optional[str] = None):
        """Initialize the template builder.
        
        Args:
            templates_dir: Path to preview_templates directory.
                         Defaults to preview_templates/ in project root.
        """
        if templates_dir is None:
            # Default to preview_templates directory in project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            templates_dir = os.path.join(current_dir, 'preview_templates')
        
        self.templates_dir = templates_dir
        self._template_cache: Dict[str, Dict[str, Any]] = {}
    
    def get_available_channels(self) -> List[str]:
        """Get list of available channels (social, email, quote).
        
        Returns:
            List of channel names
        """
        channels = []
        if os.path.exists(self.templates_dir):
            for item in os.listdir(self.templates_dir):
                item_path = os.path.join(self.templates_dir, item)
                if os.path.isdir(item_path):
                    channels.append(item)
        return sorted(channels)
    
    def get_templates_for_channel(self, channel: str) -> List[Dict[str, Any]]:
        """Get all templates for a specific channel.
        
        Args:
            channel: Channel name (social, email, or quote)
            
        Returns:
            List of template metadata (id, name, description)
        """
        channel_dir = os.path.join(self.templates_dir, channel)
        if not os.path.exists(channel_dir):
            return []
        
        templates = []
        for filename in os.listdir(channel_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(channel_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                        templates.append({
                            'id': template.get('id', filename.replace('.json', '')),
                            'name': template.get('name', filename.replace('.json', '').title()),
                            'description': template.get('description', '')
                        })
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Warning: Failed to load template {filepath}: {e}")
                    continue
        
        return templates
    
    def load_template(self, channel: str, template_id: str) -> Optional[Dict[str, Any]]:
        """Load a specific template.
        
        Args:
            channel: Channel name (social, email, or quote)
            template_id: Template ID
            
        Returns:
            Template data or None if not found
        """
        cache_key = f"{channel}/{template_id}"
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]
        
        # Try loading by ID (filename without extension)
        filepath = os.path.join(self.templates_dir, channel, f"{template_id}.json")
        
        if not os.path.exists(filepath):
            # Try finding by ID in all files
            channel_dir = os.path.join(self.templates_dir, channel)
            if os.path.exists(channel_dir):
                for filename in os.listdir(channel_dir):
                    if filename.endswith('.json'):
                        test_path = os.path.join(channel_dir, filename)
                        try:
                            with open(test_path, 'r', encoding='utf-8') as f:
                                template = json.load(f)
                                if template.get('id') == template_id:
                                    filepath = test_path
                                    break
                        except (json.JSONDecodeError, IOError):
                            continue
        
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                template = json.load(f)
                self._template_cache[cache_key] = template
                return template
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading template {filepath}: {e}")
            return None
    
    def substitute_slots(self, text: str, slots: Dict[str, str]) -> str:
        """Replace slot placeholders with actual values.
        
        Args:
            text: Text containing slot placeholders like {service}, {audience}
            slots: Dictionary mapping slot names to values
            
        Returns:
            Text with slots replaced by values
        """
        result = text
        for key, value in slots.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        return result
    
    def build_preview(
        self,
        channel: str,
        template_id: str,
        slots: Optional[Dict[str, str]] = None,
        use_baseline: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Build a preview from a template.
        
        Args:
            channel: Channel name (social, email, or quote)
            template_id: Template ID
            slots: Dictionary of slot values for personalization
            use_baseline: If True, return baseline (generic) version
            
        Returns:
            Preview content or None if template not found
        """
        template = self.load_template(channel, template_id)
        if not template:
            return None
        
        # Determine which version to use
        if use_baseline or not slots:
            content = template.get('baseline', {}).copy()
            version = 'baseline'
        else:
            content = template.get('personalized', {}).copy()
            version = 'personalized'
        
        # Apply slot substitution for personalized version
        if not use_baseline and slots:
            # Process each field in content
            for key, value in content.items():
                if isinstance(value, str):
                    content[key] = self.substitute_slots(value, slots)
                elif isinstance(value, list):
                    # Handle lists (e.g., hashtags, services)
                    content[key] = [
                        self.substitute_slots(item, slots) if isinstance(item, str) else item
                        for item in value
                    ]
                elif isinstance(value, dict):
                    # Handle nested dicts
                    content[key] = self._substitute_nested_dict(value, slots)
        
        return {
            'template_id': template_id,
            'template_name': template.get('name', ''),
            'channel': channel,
            'version': version,
            'content': content,
            'slots_used': list(slots.keys()) if slots else []
        }
    
    def _substitute_nested_dict(self, data: Dict[str, Any], slots: Dict[str, str]) -> Dict[str, Any]:
        """Recursively substitute slots in nested dictionaries.
        
        Args:
            data: Dictionary that may contain slot placeholders
            slots: Dictionary mapping slot names to values
            
        Returns:
            Dictionary with slots replaced
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.substitute_slots(value, slots)
            elif isinstance(value, list):
                result[key] = [
                    self.substitute_slots(item, slots) if isinstance(item, str) else item
                    for item in value
                ]
            elif isinstance(value, dict):
                result[key] = self._substitute_nested_dict(value, slots)
            else:
                result[key] = value
        return result
    
    def get_all_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all templates across all channels.
        
        Returns:
            Dictionary mapping channel names to lists of templates
        """
        channels = self.get_available_channels()
        result = {}
        for channel in channels:
            result[channel] = self.get_templates_for_channel(channel)
        return result
