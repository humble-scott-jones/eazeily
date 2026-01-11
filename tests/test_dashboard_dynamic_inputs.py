"""
Tests for dashboard dynamic content inputs and Surprise Me feature.

Ensures that:
1. Dashboard template renders with all dynamic input sections
2. JavaScript functions for dynamic inputs are present
3. Surprise Me button is included
4. All task types have appropriate configurations
"""

import pytest
from jinja2 import Environment, FileSystemLoader
from pathlib import Path


def test_dashboard_template_renders():
    """Test that dashboard template renders successfully."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    rendered = template.render()
    
    assert len(rendered) > 0, "Template should render content"


def test_dynamic_input_sections_present():
    """Test that all dynamic input sections are present in the template."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    rendered = template.render()
    
    # Check for each dynamic input section
    assert 'id="ad-options"' in rendered, "Ad options section should be present"
    assert 'id="linkedin-options"' in rendered, "LinkedIn options section should be present"
    assert 'id="email-options"' in rendered, "Email options section should be present"
    assert 'id="visual-options"' in rendered, "Visual/Instagram options section should be present"
    assert 'id="video-options"' in rendered, "Video options section should be present"


def test_dynamic_input_fields_present():
    """Test that specific dynamic input fields are present."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    rendered = template.render()
    
    # Ad options fields
    assert 'id="ad-objective"' in rendered, "Ad objective field should be present"
    assert 'id="ad-format"' in rendered, "Ad format field should be present"
    assert 'id="ad-audience"' in rendered, "Ad target audience field should be present"
    
    # LinkedIn options fields
    assert 'id="linkedin-type"' in rendered, "LinkedIn type field should be present"
    assert 'id="linkedin-tone"' in rendered, "LinkedIn tone modifier field should be present"
    
    # Email options fields
    assert 'id="email-subject-style"' in rendered, "Email subject style field should be present"
    assert 'id="email-cta"' in rendered, "Email CTA field should be present"
    
    # Instagram options fields
    assert 'id="instagram-format"' in rendered, "Instagram format field should be present"
    assert 'id="instagram-mood"' in rendered, "Instagram mood field should be present"
    
    # Video options fields
    assert 'id="video-length"' in rendered, "Video length field should be present"
    assert 'id="video-hook"' in rendered, "Video hook style field should be present"


def test_surprise_me_button_present():
    """Test that Surprise Me button is present."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    rendered = template.render()
    
    assert 'id="surpriseMeBtn"' in rendered, "Surprise Me button should be present"
    assert 'Surprise Me' in rendered, "Surprise Me text should be present"
    assert 'onclick="handleSurpriseMe()"' in rendered, "Surprise Me handler should be attached"


def test_dynamic_input_functions_present():
    """Test that JavaScript functions for dynamic inputs are present."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    rendered = template.render()
    
    assert 'function updateDynamicInputs()' in rendered, "updateDynamicInputs function should be present"
    assert 'function collectDynamicInputs()' in rendered, "collectDynamicInputs function should be present"
    assert 'function handleSurpriseMe()' in rendered, "handleSurpriseMe function should be present"
    assert 'DYNAMIC_INPUT_CONFIG' in rendered, "DYNAMIC_INPUT_CONFIG should be present"


def test_platform_onchange_handler():
    """Test that platform selector has onchange handler for dynamic inputs."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    rendered = template.render()
    
    # Platform selector should have onchange handler
    assert 'onchange="updateDynamicInputs()"' in rendered, "Platform selector should call updateDynamicInputs on change"


def test_task_config_includes_all_types():
    """Test that task config includes all task types."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    rendered = template.render()
    
    # Check for each task type in config
    task_types = ['post', 'ad', 'email', 'review', 'proposal', 'newsletter', 'blog', 'script', 'caption']
    for task_type in task_types:
        assert f"'{task_type}'" in rendered, f"Task type '{task_type}' should be in config"


def test_collect_dynamic_inputs_called_on_submit():
    """Test that collectDynamicInputs is called when form is submitted."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    rendered = template.render()
    
    # collectDynamicInputs should be called before API request
    assert 'collectDynamicInputs()' in rendered, "collectDynamicInputs should be called"
    # Dynamic inputs should be spread into the request body
    assert '...dynamicInputs' in rendered, "Dynamic inputs should be included in API request"


def test_surprise_me_has_topic_suggestions():
    """Test that Surprise Me function includes topic suggestions for different task types."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    rendered = template.render()
    
    # Check for topic suggestions structure
    assert 'topicSuggestions' in rendered, "Topic suggestions should be defined"
    
    # Check for some sample suggestions
    assert 'behind-the-scenes' in rendered.lower(), "Should have behind-the-scenes suggestion"
    assert 'limited time' in rendered.lower(), "Should have limited time offer suggestion"
    

def test_dynamic_sections_initially_hidden():
    """Test that dynamic input sections are initially hidden."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    rendered = template.render()
    
    # All dynamic sections should have 'hidden' class initially
    assert 'id="ad-options" class="hidden' in rendered, "Ad options should be hidden initially"
    assert 'id="linkedin-options" class="hidden' in rendered, "LinkedIn options should be hidden initially"
    assert 'id="email-options" class="hidden' in rendered, "Email options should be hidden initially"
    assert 'id="visual-options" class="hidden' in rendered, "Visual options should be hidden initially"
    assert 'id="video-options" class="hidden' in rendered, "Video options should be hidden initially"


def test_selectTask_calls_updateDynamicInputs():
    """Test that selectTask function calls updateDynamicInputs."""
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('dashboard.html')
    rendered = template.render()
    
    # In selectTask function, updateDynamicInputs should be called
    assert 'updateDynamicInputs();' in rendered, "selectTask should call updateDynamicInputs"
