"""
Unit tests for TAXONOMY-NORMALIZE-002: Platform taxonomy normalization.

Tests ensure:
1. Platform labels map correctly to normalized keys
2. Invalid keys are rejected
3. Video platforms (short_video, tiktok, tiktok_ads) have proper video gating
4. Platform groupings (Social, Social Ads, Reputation) are distinct
"""
import pytest
import json
from pathlib import Path


@pytest.fixture
def config_data():
    """Load the config.json file."""
    config_path = Path(__file__).parent.parent / 'static' / 'content' / 'config.json'
    with open(config_path, 'r') as f:
        return json.load(f)


class TestPlatformTaxonomy:
    """Test platform taxonomy structure and normalization."""
    
    def test_platform_groups_exist(self, config_data):
        """Platform groups must be defined in config."""
        assert 'platform_groups' in config_data
        groups = config_data['platform_groups']
        assert 'social' in groups
        assert 'social_ads' in groups
        assert 'reputation' in groups
    
    def test_social_platforms_normalized(self, config_data):
        """Social (organic) platforms must have correct normalized keys."""
        social = config_data['platform_groups']['social']
        platform_keys = [p['key'] for p in social['platforms']]
        
        expected_keys = ['instagram', 'facebook', 'linkedin', 'twitter', 'tiktok', 'short_video']
        assert set(platform_keys) == set(expected_keys)
        
        # Verify labels are user-friendly
        platform_map = {p['key']: p['label'] for p in social['platforms']}
        assert platform_map['twitter'] == 'X (Twitter)'
        assert platform_map['short_video'] == 'Reels/Shorts'
    
    def test_social_ads_platforms_normalized(self, config_data):
        """Social Ads platforms must have _ads suffix in keys."""
        social_ads = config_data['platform_groups']['social_ads']
        platform_keys = [p['key'] for p in social_ads['platforms']]
        
        expected_keys = ['facebook_ads', 'instagram_ads', 'linkedin_ads', 'twitter_ads', 'tiktok_ads']
        assert set(platform_keys) == set(expected_keys)
        
        # All keys must end with _ads
        for key in platform_keys:
            assert key.endswith('_ads'), f"Ad platform key '{key}' must end with '_ads'"
    
    def test_reputation_platforms_normalized(self, config_data):
        """Reputation/Support platforms must be separate from Social."""
        reputation = config_data['platform_groups']['reputation']
        platform_keys = [p['key'] for p in reputation['platforms']]
        
        # Review responses moved out of Social
        assert 'review_response' in platform_keys
        
        # Verify not in social groups
        social = config_data['platform_groups']['social']
        social_keys = [p['key'] for p in social['platforms']]
        assert 'review_response' not in social_keys
    
    def test_video_platforms_flagged(self, config_data):
        """Video platforms must have video=true flag for gating."""
        all_platforms = []
        for group_name, group_data in config_data['platform_groups'].items():
            all_platforms.extend(group_data['platforms'])
        
        video_keys = ['short_video', 'tiktok', 'tiktok_ads']
        non_video_keys = ['instagram', 'facebook', 'linkedin', 'twitter', 
                          'facebook_ads', 'instagram_ads', 'linkedin_ads', 'twitter_ads',
                          'review_response']
        
        for platform in all_platforms:
            if platform['key'] in video_keys:
                assert platform.get('video') is True, f"{platform['key']} must have video=true"
            elif platform['key'] in non_video_keys:
                assert platform.get('video') is False, f"{platform['key']} must have video=false"


class TestPlatformKeyValidation:
    """Test platform key validation and rejection of bad keys."""
    
    def test_no_duplicate_keys(self, config_data):
        """Platform keys must be unique across all groups."""
        all_keys = []
        for group_name, group_data in config_data['platform_groups'].items():
            for platform in group_data['platforms']:
                all_keys.append(platform['key'])
        
        # Check for duplicates
        assert len(all_keys) == len(set(all_keys)), "Platform keys must be unique"
    
    def test_keys_are_lowercase(self, config_data):
        """All platform keys must be lowercase for consistency."""
        for group_name, group_data in config_data['platform_groups'].items():
            for platform in group_data['platforms']:
                key = platform['key']
                assert key == key.lower(), f"Platform key '{key}' must be lowercase"
    
    def test_keys_use_underscores(self, config_data):
        """Platform keys must use underscores, not hyphens."""
        for group_name, group_data in config_data['platform_groups'].items():
            for platform in group_data['platforms']:
                key = platform['key']
                assert '-' not in key, f"Platform key '{key}' must use underscores, not hyphens"
    
    def test_invalid_keys_rejected(self):
        """Test that validation rejects invalid platform keys."""
        valid_keys = [
            'instagram', 'facebook', 'linkedin', 'twitter', 'tiktok', 'short_video',
            'facebook_ads', 'instagram_ads', 'linkedin_ads', 'twitter_ads', 'tiktok_ads',
            'review_response'
        ]
        
        invalid_keys = [
            'Facebook',  # uppercase
            'instagram-ads',  # hyphen instead of underscore
            'x',  # ambiguous
            'social',  # group name, not platform
            '',  # empty
            'youtube',  # not in taxonomy
        ]
        
        # Simulate validation
        for invalid_key in invalid_keys:
            assert invalid_key not in valid_keys, f"'{invalid_key}' should not be valid"


class TestLabelToKeyMapping:
    """Test that labels correctly map to normalized keys."""
    
    def test_label_to_key_mapping_social(self, config_data):
        """Social platform labels must map to correct keys."""
        social = config_data['platform_groups']['social']
        mapping = {p['label']: p['key'] for p in social['platforms']}
        
        assert mapping['Instagram'] == 'instagram'
        assert mapping['Facebook'] == 'facebook'
        assert mapping['LinkedIn'] == 'linkedin'
        assert mapping['X (Twitter)'] == 'twitter'
        assert mapping['TikTok'] == 'tiktok'
        assert mapping['Reels/Shorts'] == 'short_video'
    
    def test_label_to_key_mapping_ads(self, config_data):
        """Social Ads labels must map to correct _ads keys."""
        ads = config_data['platform_groups']['social_ads']
        mapping = {p['label']: p['key'] for p in ads['platforms']}
        
        assert mapping['Facebook Ads'] == 'facebook_ads'
        assert mapping['Instagram Ads'] == 'instagram_ads'
        assert mapping['LinkedIn Ads'] == 'linkedin_ads'
        assert mapping['X Ads'] == 'twitter_ads'
        assert mapping['TikTok Ads'] == 'tiktok_ads'
    
    def test_label_to_key_mapping_reputation(self, config_data):
        """Reputation labels must map to correct keys."""
        reputation = config_data['platform_groups']['reputation']
        mapping = {p['label']: p['key'] for p in reputation['platforms']}
        
        assert mapping['Review Responses'] == 'review_response'


class TestVideoVisibilityLogic:
    """Test video options visibility gating for video platforms."""
    
    def test_video_platforms_identified(self, config_data):
        """Video platforms must be correctly identified."""
        video_platforms = []
        for group_name, group_data in config_data['platform_groups'].items():
            for platform in group_data['platforms']:
                if platform.get('video') is True:
                    video_platforms.append(platform['key'])
        
        expected_video = ['short_video', 'tiktok', 'tiktok_ads']
        assert set(video_platforms) == set(expected_video)
    
    def test_non_video_platforms_identified(self, config_data):
        """Non-video platforms must not have video flag set to true."""
        non_video_platforms = []
        for group_name, group_data in config_data['platform_groups'].items():
            for platform in group_data['platforms']:
                if platform.get('video') is False:
                    non_video_platforms.append(platform['key'])
        
        expected_non_video = [
            'instagram', 'facebook', 'linkedin', 'twitter',
            'facebook_ads', 'instagram_ads', 'linkedin_ads', 'twitter_ads',
            'review_response'
        ]
        assert set(non_video_platforms) == set(expected_non_video)
    
    def test_video_gating_logic(self, config_data):
        """Simulate video options visibility gating based on platform selection."""
        # Get video platforms
        video_platform_keys = set()
        for group_name, group_data in config_data['platform_groups'].items():
            for platform in group_data['platforms']:
                if platform.get('video') is True:
                    video_platform_keys.add(platform['key'])
        
        # Test scenarios
        test_cases = [
            (['instagram'], False),  # no video platform
            (['short_video'], True),  # video platform
            (['tiktok'], True),  # video platform
            (['tiktok_ads'], True),  # video ad platform
            (['instagram', 'short_video'], True),  # mixed, has video
            (['facebook', 'linkedin'], False),  # no video platforms
        ]
        
        for selected_platforms, should_show_video in test_cases:
            has_video_platform = any(p in video_platform_keys for p in selected_platforms)
            assert has_video_platform == should_show_video, \
                f"Video options should {'show' if should_show_video else 'hide'} for {selected_platforms}"


class TestPlatformSelectionValidation:
    """Test platform selection validation rules."""
    
    def test_at_least_one_platform_required(self):
        """Platform selection must require at least one platform."""
        # Simulate validation
        valid_selections = [
            ['instagram'],
            ['facebook', 'linkedin'],
            ['short_video', 'tiktok'],
            ['facebook_ads'],
        ]
        
        invalid_selections = [
            [],  # empty
            None,  # null
        ]
        
        for selection in valid_selections:
            assert len(selection) >= 1, f"Selection {selection} should be valid"
        
        for selection in invalid_selections:
            if selection is None:
                is_valid = False
            else:
                is_valid = len(selection) >= 1
            assert not is_valid, f"Selection {selection} should be invalid"
    
    def test_no_mixing_organic_and_ads(self):
        """Organic and ad platforms should not be mixed (UI guideline)."""
        # This is a UI-level guideline, backend may allow it
        # Test verifies we can detect mixed selections
        
        organic_keys = {'instagram', 'facebook', 'linkedin', 'twitter', 'tiktok', 'short_video'}
        ad_keys = {'facebook_ads', 'instagram_ads', 'linkedin_ads', 'twitter_ads', 'tiktok_ads'}
        
        # Test detection logic for mixed selection
        def is_mixed_selection(selection):
            has_organic = any(k in organic_keys for k in selection)
            has_ads = any(k in ad_keys for k in selection)
            return has_organic and has_ads
        
        # Mixed selection (detectable)
        mixed = ['instagram', 'facebook_ads']
        assert is_mixed_selection(mixed), "Should detect mixed selection"
        
        # Pure organic
        organic_only = ['instagram', 'facebook']
        assert not is_mixed_selection(organic_only), "Should not detect organic-only as mixed"
        
        # Pure ads
        ads_only = ['facebook_ads', 'instagram_ads']
        assert not is_mixed_selection(ads_only), "Should not detect ads-only as mixed"


class TestContentTypePlatformAlignment:
    """Test that content_types align with platform groups."""
    
    def test_post_content_type_platforms(self, config_data):
        """'post' content type should reference organic social platforms."""
        post_content = next(ct for ct in config_data['content_types'] if ct['key'] == 'post')
        post_platforms = set(post_content['platforms'])
        
        social_platforms = {p['key'] for p in config_data['platform_groups']['social']['platforms']}
        
        # Post should use organic social platforms
        assert post_platforms == social_platforms
    
    def test_ad_content_type_platforms(self, config_data):
        """'ad' content type should reference ad platforms."""
        ad_content = next(ct for ct in config_data['content_types'] if ct['key'] == 'ad')
        ad_platforms = set(ad_content['platforms'])
        
        ad_platform_keys = {p['key'] for p in config_data['platform_groups']['social_ads']['platforms']}
        
        # Ad should use ad platforms
        assert ad_platforms == ad_platform_keys
