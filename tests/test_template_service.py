"""Unit tests for template_service."""

import pytest
from services.template_service import (
    get_all_templates,
    get_template_by_id,
    get_templates_by_industry,
    get_templates_by_task_type,
    get_recommended_templates,
    search_templates,
    ContentTemplate,
    RESTAURANT_TEMPLATES,
    FITNESS_TEMPLATES,
    RETAIL_TEMPLATES,
    PROFESSIONAL_TEMPLATES,
    GENERAL_TEMPLATES
)


class TestTemplateService:
    """Test suite for template service."""
    
    def test_get_all_templates_returns_list(self):
        """Test that get_all_templates returns a list."""
        templates = get_all_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0
    
    def test_get_all_templates_count(self):
        """Test that we have the expected number of templates."""
        templates = get_all_templates()
        # We should have at least 5 templates per industry (5 industries * 5 = 25+)
        assert len(templates) >= 25
    
    def test_template_has_required_fields(self):
        """Test that each template has all required fields."""
        templates = get_all_templates()
        for template in templates:
            assert hasattr(template, 'id')
            assert hasattr(template, 'name')
            assert hasattr(template, 'description')
            assert hasattr(template, 'industry')
            assert hasattr(template, 'task_type')
            assert hasattr(template, 'default_params')
            assert hasattr(template, 'example_output')
    
    def test_template_to_dict(self):
        """Test that template.to_dict() returns proper dictionary."""
        templates = get_all_templates()
        template_dict = templates[0].to_dict()
        
        assert isinstance(template_dict, dict)
        assert 'id' in template_dict
        assert 'name' in template_dict
        assert 'description' in template_dict
        assert 'industry' in template_dict
        assert 'task_type' in template_dict
        assert 'default_params' in template_dict
        assert 'example_output' in template_dict
    
    def test_get_template_by_id_valid(self):
        """Test getting a template by valid ID."""
        template = get_template_by_id('restaurant_daily_special')
        assert template is not None
        assert template.id == 'restaurant_daily_special'
        assert template.name == 'Daily Special Announcement'
    
    def test_get_template_by_id_invalid(self):
        """Test getting a template by invalid ID returns None."""
        template = get_template_by_id('nonexistent_id')
        assert template is None
    
    def test_get_templates_by_industry_restaurant(self):
        """Test getting templates for restaurant industry."""
        templates = get_templates_by_industry('restaurant')
        assert len(templates) > 0
        
        # Should include restaurant templates
        restaurant_count = sum(1 for t in templates if t.industry == 'restaurant')
        assert restaurant_count >= 5
        
        # Should also include general templates
        general_count = sum(1 for t in templates if t.industry == 'general')
        assert general_count > 0
    
    def test_get_templates_by_industry_fitness(self):
        """Test getting templates for fitness industry."""
        templates = get_templates_by_industry('fitness')
        assert len(templates) > 0
        
        fitness_count = sum(1 for t in templates if t.industry == 'fitness')
        assert fitness_count >= 5
    
    def test_get_templates_by_industry_general_fallback(self):
        """Test that unknown industry gets general templates."""
        templates = get_templates_by_industry('unknown_industry')
        assert len(templates) > 0
        # Should only return general templates
        assert all(t.industry == 'general' for t in templates)
    
    def test_get_templates_by_task_type_post(self):
        """Test getting templates by task type 'post'."""
        templates = get_templates_by_task_type('post')
        assert len(templates) > 0
        assert all(t.task_type == 'post' for t in templates)
    
    def test_get_templates_by_task_type_script(self):
        """Test getting templates by task type 'script'."""
        templates = get_templates_by_task_type('script')
        assert len(templates) > 0
        assert all(t.task_type == 'script' for t in templates)
    
    def test_get_recommended_templates_no_filters(self):
        """Test getting recommended templates with no filters."""
        templates = get_recommended_templates()
        assert len(templates) > 0
        # Should return all templates
        assert len(templates) == len(get_all_templates())
    
    def test_get_recommended_templates_with_industry(self):
        """Test getting recommended templates filtered by industry."""
        templates = get_recommended_templates(industry='restaurant')
        assert len(templates) > 0
        
        # Should include restaurant and general templates
        industries = {t.industry for t in templates}
        assert 'restaurant' in industries or 'general' in industries
    
    def test_get_recommended_templates_with_task_type(self):
        """Test getting recommended templates filtered by task type."""
        templates = get_recommended_templates(task_type='post')
        assert len(templates) > 0
        assert all(t.task_type == 'post' for t in templates)
    
    def test_get_recommended_templates_with_both_filters(self):
        """Test getting recommended templates with both filters."""
        templates = get_recommended_templates(industry='fitness', task_type='post')
        assert len(templates) > 0
        
        # All should be posts
        assert all(t.task_type == 'post' for t in templates)
        
        # Should be fitness or general
        assert all(t.industry in ['fitness', 'general'] for t in templates)
    
    def test_search_templates_by_name(self):
        """Test searching templates by name."""
        templates = search_templates('motivation')
        assert len(templates) > 0
        
        # Should find Monday Motivation template
        names = [t.name.lower() for t in templates]
        assert any('motivation' in name for name in names)
    
    def test_search_templates_by_description(self):
        """Test searching templates by description."""
        templates = search_templates('announcement')
        assert len(templates) > 0
        
        # Check that at least one has 'announcement' in name or description
        texts = [t.name.lower() + ' ' + t.description.lower() for t in templates]
        assert any('announcement' in text for text in texts)
    
    def test_search_templates_case_insensitive(self):
        """Test that search is case insensitive."""
        templates_lower = search_templates('daily')
        templates_upper = search_templates('DAILY')
        
        assert len(templates_lower) == len(templates_upper)
    
    def test_restaurant_templates_count(self):
        """Test that we have the expected number of restaurant templates."""
        assert len(RESTAURANT_TEMPLATES) >= 5
    
    def test_fitness_templates_count(self):
        """Test that we have the expected number of fitness templates."""
        assert len(FITNESS_TEMPLATES) >= 5
    
    def test_retail_templates_count(self):
        """Test that we have the expected number of retail templates."""
        assert len(RETAIL_TEMPLATES) >= 5
    
    def test_professional_templates_count(self):
        """Test that we have the expected number of professional templates."""
        assert len(PROFESSIONAL_TEMPLATES) >= 5
    
    def test_general_templates_count(self):
        """Test that we have the expected number of general templates."""
        assert len(GENERAL_TEMPLATES) >= 5
    
    def test_template_ids_unique(self):
        """Test that all template IDs are unique."""
        templates = get_all_templates()
        ids = [t.id for t in templates]
        assert len(ids) == len(set(ids)), "Template IDs must be unique"
    
    def test_template_default_params_structure(self):
        """Test that default_params have expected structure."""
        templates = get_all_templates()
        
        for template in templates:
            assert isinstance(template.default_params, dict)
            
            # Post templates should have platform
            if template.task_type == 'post':
                assert 'platform' in template.default_params or 'topic' in template.default_params
            
            # Script templates should have video-related params
            if template.task_type == 'script':
                assert 'topic' in template.default_params
    
    def test_template_example_output_not_empty(self):
        """Test that all templates have non-empty example output."""
        templates = get_all_templates()
        
        for template in templates:
            assert template.example_output
            assert len(template.example_output) > 20, f"Template {template.id} has too short example"
