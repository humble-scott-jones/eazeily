"""Tests for template_service module."""

import pytest
from services.template_service import (
    get_templates_for_industry,
    get_template_by_index,
    format_template_list,
    get_available_industries,
    INDUSTRY_TEMPLATES
)


class TestTemplateService:
    """Test suite for template_service."""
    
    def test_get_templates_for_restaurant(self):
        """Test getting templates for restaurant industry."""
        templates = get_templates_for_industry('restaurant')
        
        assert len(templates) == 5
        assert templates[0]['name'] == 'Daily Special'
        assert templates[0]['topic'] == "today's special dish"
        assert templates[0]['mood'] == 'excited'
    
    def test_get_templates_for_fitness(self):
        """Test getting templates for fitness industry."""
        templates = get_templates_for_industry('fitness')
        
        assert len(templates) == 5
        assert templates[0]['name'] == 'Monday Motivation'
        assert templates[0]['mood'] == 'inspiring'
    
    def test_get_templates_for_unknown_industry_returns_default(self):
        """Test that unknown industry returns default templates."""
        templates = get_templates_for_industry('unknown_industry')
        
        assert len(templates) == 5
        assert templates[0]['name'] == 'Weekly Update'
    
    def test_get_templates_for_none_returns_default(self):
        """Test that None industry returns default templates."""
        templates = get_templates_for_industry(None)
        
        assert len(templates) == 5
        assert templates[0]['name'] == 'Weekly Update'
    
    def test_get_templates_case_insensitive(self):
        """Test that industry name is case insensitive."""
        templates_lower = get_templates_for_industry('restaurant')
        templates_upper = get_templates_for_industry('RESTAURANT')
        templates_mixed = get_templates_for_industry('ReStAuRaNt')
        
        assert templates_lower == templates_upper == templates_mixed
    
    def test_get_template_by_index_valid(self):
        """Test getting a specific template by index."""
        template = get_template_by_index('fitness', 1)
        
        assert template is not None
        assert template['name'] == 'Monday Motivation'
        assert template['mood'] == 'inspiring'
    
    def test_get_template_by_index_last(self):
        """Test getting the last template."""
        template = get_template_by_index('restaurant', 5)
        
        assert template is not None
        assert template['name'] == 'New Menu Item'
    
    def test_get_template_by_index_out_of_range(self):
        """Test that out of range index returns None."""
        template = get_template_by_index('restaurant', 0)
        assert template is None
        
        template = get_template_by_index('restaurant', 6)
        assert template is None
        
        template = get_template_by_index('restaurant', -1)
        assert template is None
    
    def test_format_template_list_includes_all_templates(self):
        """Test that formatted list includes all templates."""
        formatted = format_template_list('restaurant')
        
        assert '**Quick Templates:**' in formatted
        assert '1. **Daily Special**' in formatted
        assert '5. **New Menu Item**' in formatted
        assert 'Reply with a number (1-5)' in formatted
    
    def test_format_template_list_for_default(self):
        """Test formatting default templates."""
        formatted = format_template_list(None)
        
        assert '**Quick Templates:**' in formatted
        assert '1. **Weekly Update**' in formatted
    
    def test_get_available_industries(self):
        """Test getting list of available industries."""
        industries = get_available_industries()
        
        assert 'restaurant' in industries
        assert 'fitness' in industries
        assert 'retail' in industries
        assert 'salon' in industries
        assert 'software' in industries
        assert 'default' not in industries  # Should exclude 'default'
    
    def test_all_industries_have_five_templates(self):
        """Test that all industries have exactly 5 templates."""
        for industry in INDUSTRY_TEMPLATES.keys():
            templates = INDUSTRY_TEMPLATES[industry]
            assert len(templates) == 5, f"Industry '{industry}' should have 5 templates"
    
    def test_all_templates_have_required_fields(self):
        """Test that all templates have name, topic, and mood."""
        for industry, templates in INDUSTRY_TEMPLATES.items():
            for i, template in enumerate(templates, 1):
                assert 'name' in template, f"Template {i} in {industry} missing 'name'"
                assert 'topic' in template, f"Template {i} in {industry} missing 'topic'"
                assert 'mood' in template, f"Template {i} in {industry} missing 'mood'"
                
                # Check that fields are non-empty
                assert template['name'], f"Template {i} in {industry} has empty 'name'"
                assert template['topic'], f"Template {i} in {industry} has empty 'topic'"
                assert template['mood'], f"Template {i} in {industry} has empty 'mood'"
