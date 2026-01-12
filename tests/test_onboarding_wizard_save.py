# """
# Test suite for onboarding wizard form save functionality.
# 
# NOTE: These tests are commented out as the onboarding wizard is no longer in use.
# The tests remain here for reference and can be re-enabled if the wizard is brought back.
# 
# Validates that the onboarding wizard form (Step 2):
# 1. Saves profile data correctly to the database
# 2. Redirects to dashboard on success
# 3. Validates required fields
# 4. Handles errors gracefully
# """
# import pytest


# def test_onboarding_wizard_save_success(client):
#     """Onboarding wizard form POST saves profile and redirects to dashboard."""
#     # Create and login user
#     signup_response = client.post('/api/signup', json={
#         'email': 'onboarding_test@example.com',
#         'password': 'testpass123'
#     })
#     assert signup_response.status_code in (200, 201)
#     
#     # Submit onboarding form with all required fields
#     form_data = {
#         'business_name': 'Smith Real Estate',
#         'industry': 'Realtor / Real Estate',
#         'target_audience': 'Local families looking to upsize, first-time home buyers',
#         'brand_voice': 'Professional, reassuring, and expert-level',
#         'key_offer': 'Free Home Valuation Report',
#         'voice_rules': 'No exclamation points',
#         'writing_samples': 'Just closed on another dream home! 🏡 Congrats to the Martinez family!\n\nLooking to sell? Let\'s chat about what your home is worth in today\'s market.'
#     }
#     
#     save_response = client.post('/onboarding', data=form_data, follow_redirects=False)
#     
#     # Should redirect to dashboard on success
#     assert save_response.status_code == 302
#     assert '/dashboard' in save_response.location
#     
#     # Verify profile was saved by fetching via API
#     fetch_response = client.get('/api/profile')
#     assert fetch_response.status_code == 200
#     profile = fetch_response.get_json()['profile']
#     
#     # Verify all fields persisted correctly
#     assert profile['company'] == 'Smith Real Estate'
#     assert profile['industry'] == 'Realtor / Real Estate'
#     assert profile['target_audience'] == 'Local families looking to upsize, first-time home buyers'
#     assert profile['brand_voice'] == 'Professional, reassuring, and expert-level'
#     assert profile['tone'] == 'Professional, reassuring, and expert-level'  # brand_voice maps to tone
#     assert profile['key_offer'] == 'Free Home Valuation Report'
#     assert profile['voice_rules'] == 'No exclamation points'
#     assert len(profile['writing_samples']) == 2  # Split by blank line


# def test_onboarding_wizard_requires_all_fields(client):
#     """Onboarding wizard validates required fields."""
#     # Create and login user
#     signup_response = client.post('/api/signup', json={
#         'email': 'validation_test@example.com',
#         'password': 'testpass123'
#     })
#     assert signup_response.status_code in (200, 201)
#     
#     # Submit with missing required field
#     form_data = {
#         'business_name': 'Test Company',
#         'industry': 'Software / Tech / Startup',
#         # Missing target_audience (required)
#         'brand_voice': 'Professional',
#         'key_offer': 'Best software',
#         'writing_samples': 'Sample 1\n\nSample 2'
#     }
#     
#     save_response = client.post('/onboarding', data=form_data)
#     
#     # Should return 400 with validation error
#     assert save_response.status_code == 400
#     # Response should still render the form (not redirect)
#     assert b'onboarding' in save_response.data.lower() or b'wizard' in save_response.data.lower()


# def test_onboarding_wizard_updates_existing_profile(client):
#     """Onboarding wizard updates existing profile without creating duplicates."""
#     # Create and login user
#     signup_response = client.post('/api/signup', json={
#         'email': 'update_test@example.com',
#         'password': 'testpass123'
#     })
#     assert signup_response.status_code in (200, 201)
#     
#     # First submission
#     form_data_1 = {
#         'business_name': 'Original Business',
#         'industry': 'Software / Tech / Startup',
#         'target_audience': 'Developers',
#         'brand_voice': 'Technical',
#         'key_offer': 'Free trial',
#         'writing_samples': 'Sample 1\n\nSample 2'
#     }
#     save_response_1 = client.post('/onboarding', data=form_data_1, follow_redirects=False)
#     assert save_response_1.status_code == 302
#     
#     # Get profile ID
#     fetch_1 = client.get('/api/profile')
#     profile_1 = fetch_1.get_json()['profile']
#     original_id = profile_1['id']
#     
#     # Second submission (update)
#     form_data_2 = {
#         'business_name': 'Updated Business',
#         'industry': 'Realtor / Real Estate',
#         'target_audience': 'Home buyers',
#         'brand_voice': 'Friendly',
#         'key_offer': 'Free consultation',
#         'writing_samples': 'Updated sample'
#     }
#     save_response_2 = client.post('/onboarding', data=form_data_2, follow_redirects=False)
#     assert save_response_2.status_code == 302
#     
#     # Verify same profile ID (not a duplicate)
#     fetch_2 = client.get('/api/profile')
#     profile_2 = fetch_2.get_json()['profile']
#     assert profile_2['id'] == original_id
#     
#     # Verify fields were updated
#     assert profile_2['company'] == 'Updated Business'
#     assert profile_2['industry'] == 'Realtor / Real Estate'


# def test_onboarding_wizard_splits_writing_samples(client):
#     """Onboarding wizard correctly splits writing samples by blank lines."""
#     # Create and login user
#     signup_response = client.post('/api/signup', json={
#         'email': 'samples_test@example.com',
#         'password': 'testpass123'
#     })
#     assert signup_response.status_code in (200, 201)
#     
#     # Submit with multiple samples separated by blank lines
#     form_data = {
#         'business_name': 'Test Business',
#         'industry': 'Software / Tech / Startup',
#         'target_audience': 'Developers',
#         'brand_voice': 'Professional',
#         'key_offer': 'Free trial',
#         'writing_samples': 'First sample here.\n\nSecond sample here.\n\nThird sample here.'
#     }
#     
#     save_response = client.post('/onboarding', data=form_data, follow_redirects=False)
#     assert save_response.status_code == 302
#     
#     # Verify samples were split correctly
#     fetch_response = client.get('/api/profile')
#     profile = fetch_response.get_json()['profile']
#     
#     assert len(profile['writing_samples']) == 3
#     assert profile['writing_samples'][0] == 'First sample here.'
#     assert profile['writing_samples'][1] == 'Second sample here.'
#     assert profile['writing_samples'][2] == 'Third sample here.'


# def test_onboarding_wizard_handles_optional_fields(client):
#     """Onboarding wizard saves profile with optional voice_rules field empty."""
#     # Create and login user
#     signup_response = client.post('/api/signup', json={
#         'email': 'optional_test@example.com',
#         'password': 'testpass123'
#     })
#     assert signup_response.status_code in (200, 201)
#     
#     # Submit without optional voice_rules
#     form_data = {
#         'business_name': 'Test Business',
#         'industry': 'Software / Tech / Startup',
#         'target_audience': 'Developers',
#         'brand_voice': 'Professional',
#         'key_offer': 'Free trial',
#         # voice_rules is optional - not included
#         'writing_samples': 'Sample text'
#     }
#     
#     save_response = client.post('/onboarding', data=form_data, follow_redirects=False)
#     assert save_response.status_code == 302
#     
#     # Verify profile was saved
#     fetch_response = client.get('/api/profile')
#     profile = fetch_response.get_json()['profile']
#     
#     assert profile['company'] == 'Test Business'
#     assert profile['voice_rules'] == ''  # Optional field should be empty string
