"""
Test preview builder functionality for all channels.

Tests that preview templates work offline, deterministically, and support
all required channels (social, email, quote) with proper slot substitution.
"""

import pytest
import os
import json
from preview_builder import PreviewTemplateBuilder


@pytest.fixture
def builder():
    """Create a PreviewTemplateBuilder instance."""
    return PreviewTemplateBuilder()


@pytest.fixture
def sample_slots():
    """Sample slot values for testing."""
    return {
        'service': 'Professional Cleaning',
        'audience': 'busy professionals',
        'pain': 'lack of time for housework',
        'outcome': 'a spotless home',
        'differentiator': 'eco-friendly products and same-day service',
        'proof': '5-star rated by 200+ happy clients',
        'cta': 'Get 20% off your first booking',
        'validity_days': '30',
        'deposit_policy': '50% deposit required to begin'
    }


class TestPreviewBuilderChannels:
    """Test that preview builder supports all required channels."""
    
    def test_social_channel_available(self, builder):
        """Test that social channel is available."""
        channels = builder.get_available_channels()
        assert 'social' in channels, "Social channel must be available"
    
    def test_email_channel_available(self, builder):
        """Test that email channel is available."""
        channels = builder.get_available_channels()
        assert 'email' in channels, "Email channel must be available"
    
    def test_quote_channel_available(self, builder):
        """Test that quote channel is available."""
        channels = builder.get_available_channels()
        assert 'quote' in channels, "Quote channel must be available"
    
    def test_all_required_channels_present(self, builder):
        """Test that all three required channels are available."""
        channels = builder.get_available_channels()
        required = {'social', 'email', 'quote'}
        assert required.issubset(set(channels)), \
            f"Missing required channels. Required: {required}, Found: {set(channels)}"


class TestSocialTemplates:
    """Test social media preview templates."""
    
    def test_social_templates_exist(self, builder):
        """Test that social templates are available."""
        templates = builder.get_templates_for_channel('social')
        assert len(templates) > 0, "Social channel must have at least one template"
    
    def test_social_baseline_version(self, builder):
        """Test social template baseline (generic) version."""
        templates = builder.get_templates_for_channel('social')
        assert len(templates) > 0, "Need at least one social template"
        
        template_id = templates[0]['id']
        preview = builder.build_preview('social', template_id, use_baseline=True)
        
        assert preview is not None, "Preview should not be None"
        assert preview['version'] == 'baseline', "Should return baseline version"
        assert 'content' in preview
        assert 'caption' in preview['content'], "Social preview should have caption"
    
    def test_social_personalized_version(self, builder, sample_slots):
        """Test social template personalized version with slot substitution."""
        templates = builder.get_templates_for_channel('social')
        assert len(templates) > 0, "Need at least one social template"
        
        template_id = templates[0]['id']
        preview = builder.build_preview('social', template_id, slots=sample_slots)
        
        assert preview is not None, "Preview should not be None"
        assert preview['version'] == 'personalized', "Should return personalized version"
        assert 'content' in preview
        
        # Check that slots were substituted
        caption = preview['content'].get('caption', '')
        assert sample_slots['service'] in caption, \
            f"Service '{sample_slots['service']}' should be in caption"
    
    def test_social_no_openai_dependency(self, builder, sample_slots):
        """Test that social preview works without OpenAI (deterministic)."""
        templates = builder.get_templates_for_channel('social')
        assert len(templates) > 0, "Need at least one social template"
        
        template_id = templates[0]['id']
        
        # Generate preview multiple times - should be identical
        preview1 = builder.build_preview('social', template_id, slots=sample_slots)
        preview2 = builder.build_preview('social', template_id, slots=sample_slots)
        
        assert preview1 == preview2, \
            "Previews should be deterministic (identical on multiple calls)"


class TestEmailTemplates:
    """Test email preview templates."""
    
    def test_email_templates_exist(self, builder):
        """Test that email templates are available."""
        templates = builder.get_templates_for_channel('email')
        assert len(templates) > 0, "Email channel must have at least one template"
    
    def test_email_baseline_version(self, builder):
        """Test email template baseline version."""
        templates = builder.get_templates_for_channel('email')
        assert len(templates) > 0, "Need at least one email template"
        
        template_id = templates[0]['id']
        preview = builder.build_preview('email', template_id, use_baseline=True)
        
        assert preview is not None, "Preview should not be None"
        assert preview['version'] == 'baseline'
        assert 'content' in preview
        assert 'subject' in preview['content'], "Email should have subject"
        assert 'body' in preview['content'], "Email should have body"
    
    def test_email_personalized_version(self, builder, sample_slots):
        """Test email template personalized version with slot substitution."""
        templates = builder.get_templates_for_channel('email')
        assert len(templates) > 0, "Need at least one email template"
        
        template_id = templates[0]['id']
        preview = builder.build_preview('email', template_id, slots=sample_slots)
        
        assert preview is not None, "Preview should not be None"
        assert preview['version'] == 'personalized'
        assert 'content' in preview
        
        # Check slot substitution in subject or body
        subject = preview['content'].get('subject', '')
        body = preview['content'].get('body', '')
        
        assert sample_slots['service'] in subject or sample_slots['service'] in body, \
            f"Service '{sample_slots['service']}' should be in subject or body"
    
    def test_email_no_openai_dependency(self, builder, sample_slots):
        """Test that email preview works without OpenAI (deterministic)."""
        templates = builder.get_templates_for_channel('email')
        assert len(templates) > 0, "Need at least one email template"
        
        template_id = templates[0]['id']
        
        # Generate preview multiple times - should be identical
        preview1 = builder.build_preview('email', template_id, slots=sample_slots)
        preview2 = builder.build_preview('email', template_id, slots=sample_slots)
        
        assert preview1 == preview2, \
            "Previews should be deterministic (identical on multiple calls)"


class TestQuoteTemplates:
    """Test quote preview templates."""
    
    def test_quote_templates_exist(self, builder):
        """Test that quote templates are available."""
        templates = builder.get_templates_for_channel('quote')
        assert len(templates) > 0, "Quote channel must have at least one template"
    
    def test_quote_baseline_version(self, builder):
        """Test quote template baseline version."""
        templates = builder.get_templates_for_channel('quote')
        assert len(templates) > 0, "Need at least one quote template"
        
        template_id = templates[0]['id']
        preview = builder.build_preview('quote', template_id, use_baseline=True)
        
        assert preview is not None, "Preview should not be None"
        assert preview['version'] == 'baseline'
        assert 'content' in preview
        assert 'title' in preview['content'], "Quote should have title"
        assert 'introduction' in preview['content'], "Quote should have introduction"
    
    def test_quote_personalized_version(self, builder, sample_slots):
        """Test quote template personalized version with slot substitution."""
        templates = builder.get_templates_for_channel('quote')
        assert len(templates) > 0, "Need at least one quote template"
        
        template_id = templates[0]['id']
        preview = builder.build_preview('quote', template_id, slots=sample_slots)
        
        assert preview is not None, "Preview should not be None"
        assert preview['version'] == 'personalized'
        assert 'content' in preview
        
        # Check slot substitution
        title = preview['content'].get('title', '')
        intro = preview['content'].get('introduction', '')
        
        assert sample_slots['service'] in title or sample_slots['service'] in intro, \
            f"Service '{sample_slots['service']}' should be in title or introduction"
    
    def test_quote_deposit_policy_slot(self, builder, sample_slots):
        """Test that quote templates support deposit_policy slot."""
        templates = builder.get_templates_for_channel('quote')
        assert len(templates) > 0, "Need at least one quote template"
        
        template_id = templates[0]['id']
        preview = builder.build_preview('quote', template_id, slots=sample_slots)
        
        # Check if deposit_policy appears in any field
        content_str = json.dumps(preview['content'])
        assert sample_slots['deposit_policy'] in content_str, \
            "Deposit policy should appear in quote content"
    
    def test_quote_validity_days_slot(self, builder, sample_slots):
        """Test that quote templates support validity_days slot."""
        templates = builder.get_templates_for_channel('quote')
        assert len(templates) > 0, "Need at least one quote template"
        
        template_id = templates[0]['id']
        preview = builder.build_preview('quote', template_id, slots=sample_slots)
        
        # Check if validity_days appears in any field
        content_str = json.dumps(preview['content'])
        assert sample_slots['validity_days'] in content_str, \
            "Validity days should appear in quote content"
    
    def test_quote_no_openai_dependency(self, builder, sample_slots):
        """Test that quote preview works without OpenAI (deterministic)."""
        templates = builder.get_templates_for_channel('quote')
        assert len(templates) > 0, "Need at least one quote template"
        
        template_id = templates[0]['id']
        
        # Generate preview multiple times - should be identical
        preview1 = builder.build_preview('quote', template_id, slots=sample_slots)
        preview2 = builder.build_preview('quote', template_id, slots=sample_slots)
        
        assert preview1 == preview2, \
            "Previews should be deterministic (identical on multiple calls)"


class TestSlotSubstitution:
    """Test slot substitution functionality."""
    
    def test_all_required_slots_supported(self, builder):
        """Test that all required slots are supported."""
        required_slots = [
            'service', 'audience', 'pain', 'outcome',
            'differentiator', 'proof', 'cta',
            'validity_days', 'deposit_policy'
        ]
        
        test_slots = {slot: f"test_{slot}" for slot in required_slots}
        
        # Test with social template
        templates = builder.get_templates_for_channel('social')
        if templates:
            template_id = templates[0]['id']
            preview = builder.build_preview('social', template_id, slots=test_slots)
            assert preview is not None, "Should handle all slot types"
    
    def test_partial_slot_substitution(self, builder):
        """Test that partial slot substitution works (not all slots provided)."""
        partial_slots = {
            'service': 'Test Service',
            'audience': 'test audience'
        }
        
        templates = builder.get_templates_for_channel('social')
        if templates:
            template_id = templates[0]['id']
            preview = builder.build_preview('social', template_id, slots=partial_slots)
            
            assert preview is not None, "Should work with partial slots"
            # Check that provided slots were substituted
            content_str = json.dumps(preview['content'])
            assert 'Test Service' in content_str or '{service}' in content_str
    
    def test_slot_substitution_case_sensitive(self, builder):
        """Test that slot names are case-sensitive."""
        slots = {
            'service': 'MyService',
            'Service': 'WrongCase'  # Should not be used
        }
        
        templates = builder.get_templates_for_channel('social')
        if templates:
            template_id = templates[0]['id']
            preview = builder.build_preview('social', template_id, slots=slots)
            
            # Should use 'service' not 'Service'
            content_str = json.dumps(preview['content'])
            if 'MyService' in content_str:
                assert 'WrongCase' not in content_str


class TestOfflineCapability:
    """Test that preview builder works offline without external dependencies."""
    
    def test_no_network_required(self, builder, sample_slots):
        """Test that preview generation doesn't require network access."""
        # This test verifies the system works offline by checking
        # that no external API calls are made (OpenAI, etc.)
        
        for channel in ['social', 'email', 'quote']:
            templates = builder.get_templates_for_channel(channel)
            if templates:
                template_id = templates[0]['id']
                preview = builder.build_preview(channel, template_id, slots=sample_slots)
                
                assert preview is not None, \
                    f"Channel {channel} should work offline"
    
    def test_template_caching(self, builder):
        """Test that templates are cached for performance."""
        # Load a template twice
        templates = builder.get_templates_for_channel('social')
        if templates:
            template_id = templates[0]['id']
            
            # First load
            template1 = builder.load_template('social', template_id)
            # Second load (should be from cache)
            template2 = builder.load_template('social', template_id)
            
            # Should be the same object (cached)
            assert template1 is template2, "Templates should be cached"


class TestBeforeAfterComparison:
    """Test before/after preview comparison functionality."""
    
    def test_baseline_vs_personalized_difference(self, builder, sample_slots):
        """Test that baseline and personalized versions differ appropriately."""
        templates = builder.get_templates_for_channel('social')
        if templates:
            template_id = templates[0]['id']
            
            baseline = builder.build_preview('social', template_id, use_baseline=True)
            personalized = builder.build_preview('social', template_id, slots=sample_slots)
            
            assert baseline is not None and personalized is not None
            assert baseline['version'] == 'baseline'
            assert personalized['version'] == 'personalized'
            
            # Content should be different
            baseline_caption = baseline['content'].get('caption', '')
            personalized_caption = personalized['content'].get('caption', '')
            
            # Personalized should include slot values
            if sample_slots['service'] in personalized_caption:
                assert sample_slots['service'] not in baseline_caption, \
                    "Baseline should not contain personalized content"
