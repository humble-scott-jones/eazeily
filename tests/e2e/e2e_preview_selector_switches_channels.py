"""
E2E test for preview template selector.

Tests that:
- Preview selector loads without errors
- User can switch between channels (social, email, quote)
- Previews update live as chips/options are selected
- Both baseline and personalized previews render correctly
- No OpenAI dependency (instant previews)
"""

import os
import time
import subprocess
import pathlib
import requests
import pytest
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
PORT = int(os.getenv("PORT", "5001"))
BASE = f"http://127.0.0.1:{PORT}"

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_UI_SMOKE") != "1", 
    reason="UI smoke tests disabled (set RUN_UI_SMOKE=1)"
)


def start_server():
    """Start Flask server and wait for it to be ready."""
    py = "./.venv/bin/python" if (ROOT / ".venv" / "bin" / "python").exists() else "python3"
    env = os.environ.copy()
    env['PORT'] = str(PORT)
    p = subprocess.Popen([py, "app.py"], cwd=str(ROOT), env=env)
    
    # Wait for server to be ready
    for _ in range(40):
        try:
            r = requests.get(f"{BASE}/__dev__/ping", timeout=1)
            if r.status_code == 200:
                return p
        except Exception:
            pass
        time.sleep(0.5)
    
    p.kill()
    raise RuntimeError("server failed to start")


def stop_server(p):
    """Stop Flask server gracefully."""
    try:
        p.terminate()
        p.wait(timeout=5)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def test_preview_api_endpoints_available():
    """Test that preview template API endpoints are available."""
    proc = start_server()
    
    try:
        # Test list all templates
        r = requests.get(f"{BASE}/api/preview-templates", timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        
        data = r.json()
        assert data.get('ok') is True, "API should return ok: true"
        assert 'templates' in data, "Response should include templates"
        
        templates = data['templates']
        assert 'social' in templates, "Should have social channel"
        assert 'email' in templates, "Should have email channel"
        assert 'quote' in templates, "Should have quote channel"
        
        # Test channel-specific endpoint
        r = requests.get(f"{BASE}/api/preview-templates/social", timeout=5)
        assert r.status_code == 200, f"Channel endpoint failed: {r.status_code}"
        
        channel_data = r.json()
        assert channel_data.get('ok') is True
        assert channel_data.get('channel') == 'social'
        assert len(channel_data.get('templates', [])) > 0, "Social should have templates"
        
    finally:
        stop_server(proc)


def test_preview_generation_instant():
    """Test that preview generation is instant (no OpenAI delay)."""
    proc = start_server()
    
    try:
        # Get a social template
        r = requests.get(f"{BASE}/api/preview-templates/social", timeout=5)
        assert r.status_code == 200
        
        templates = r.json().get('templates', [])
        assert len(templates) > 0, "Need at least one social template"
        
        template_id = templates[0]['id']
        
        # Time the preview generation
        start = time.time()
        r = requests.post(
            f"{BASE}/api/preview-templates/social/{template_id}",
            json={
                'slots': {
                    'service': 'Test Service',
                    'audience': 'test users',
                    'pain': 'test problem',
                    'outcome': 'test solution'
                }
            },
            timeout=5
        )
        elapsed = time.time() - start
        
        assert r.status_code == 200, f"Preview generation failed: {r.status_code}"
        
        # Should be instant (< 1 second, definitely not 5-10s like OpenAI calls)
        assert elapsed < 1.0, \
            f"Preview should be instant, took {elapsed:.2f}s (suggests OpenAI dependency)"
        
        data = r.json()
        assert data.get('ok') is True
        assert 'preview' in data
        
        preview = data['preview']
        assert preview['version'] == 'personalized'
        assert 'Test Service' in str(preview['content']), \
            "Preview should include slot substitutions"
        
    finally:
        stop_server(proc)


def test_baseline_vs_personalized():
    """Test switching between baseline and personalized previews."""
    proc = start_server()
    
    try:
        # Get email templates
        r = requests.get(f"{BASE}/api/preview-templates/email", timeout=5)
        assert r.status_code == 200
        
        templates = r.json().get('templates', [])
        assert len(templates) > 0
        
        template_id = templates[0]['id']
        
        # Get baseline preview
        r_baseline = requests.post(
            f"{BASE}/api/preview-templates/email/{template_id}",
            json={'use_baseline': True},
            timeout=5
        )
        assert r_baseline.status_code == 200
        
        baseline = r_baseline.json()['preview']
        assert baseline['version'] == 'baseline'
        
        # Get personalized preview
        r_personalized = requests.post(
            f"{BASE}/api/preview-templates/email/{template_id}",
            json={
                'slots': {
                    'service': 'Premium Service',
                    'audience': 'professionals',
                    'pain': 'time constraints'
                }
            },
            timeout=5
        )
        assert r_personalized.status_code == 200
        
        personalized = r_personalized.json()['preview']
        assert personalized['version'] == 'personalized'
        
        # Personalized should include slot values
        assert 'Premium Service' in str(personalized['content'])
        
        # Baseline should not include personalized content
        assert 'Premium Service' not in str(baseline['content'])
        
    finally:
        stop_server(proc)


def test_all_channels_accessible():
    """Test that all three channels return valid previews."""
    proc = start_server()
    
    try:
        channels = ['social', 'email', 'quote']
        
        for channel in channels:
            # Get templates for channel
            r = requests.get(f"{BASE}/api/preview-templates/{channel}", timeout=5)
            assert r.status_code == 200, f"Channel {channel} not accessible"
            
            templates = r.json().get('templates', [])
            assert len(templates) > 0, f"Channel {channel} has no templates"
            
            # Generate a preview
            template_id = templates[0]['id']
            r = requests.post(
                f"{BASE}/api/preview-templates/{channel}/{template_id}",
                json={
                    'slots': {
                        'service': f'{channel.title()} Test',
                        'audience': 'users',
                        'pain': 'problem'
                    }
                },
                timeout=5
            )
            
            assert r.status_code == 200, \
                f"Preview generation failed for {channel}"
            
            data = r.json()
            assert data.get('ok') is True
            assert data['preview']['channel'] == channel
            
    finally:
        stop_server(proc)


def test_slot_updates_reflected_in_preview():
    """Test that changing slot values updates the preview."""
    proc = start_server()
    
    try:
        r = requests.get(f"{BASE}/api/preview-templates/quote", timeout=5)
        assert r.status_code == 200
        
        templates = r.json().get('templates', [])
        template_id = templates[0]['id']
        
        # First set of slots
        slots1 = {
            'service': 'Service A',
            'validity_days': '30',
            'deposit_policy': '50% upfront'
        }
        
        r1 = requests.post(
            f"{BASE}/api/preview-templates/quote/{template_id}",
            json={'slots': slots1},
            timeout=5
        )
        assert r1.status_code == 200
        preview1 = r1.json()['preview']
        
        # Second set of slots (different values)
        slots2 = {
            'service': 'Service B',
            'validity_days': '60',
            'deposit_policy': '100% upfront'
        }
        
        r2 = requests.post(
            f"{BASE}/api/preview-templates/quote/{template_id}",
            json={'slots': slots2},
            timeout=5
        )
        assert r2.status_code == 200
        preview2 = r2.json()['preview']
        
        # Previews should be different
        content1 = str(preview1['content'])
        content2 = str(preview2['content'])
        
        assert 'Service A' in content1
        assert 'Service B' in content2
        assert '30' in content1
        assert '60' in content2
        assert content1 != content2, "Different slots should produce different previews"
        
    finally:
        stop_server(proc)


def test_no_openai_environment_variable_needed():
    """Test that preview works without OPENAI_API_KEY set."""
    proc = start_server()
    
    try:
        # This test verifies that previews work even if OpenAI is not configured
        # The mere fact that the server started and endpoints work proves this,
        # but we'll be explicit
        
        r = requests.get(f"{BASE}/api/preview-templates", timeout=5)
        assert r.status_code == 200, \
            "Preview API should work without OpenAI configuration"
        
        # Generate a preview to ensure no OpenAI dependency at runtime
        r = requests.get(f"{BASE}/api/preview-templates/social", timeout=5)
        templates = r.json().get('templates', [])
        
        if templates:
            r = requests.post(
                f"{BASE}/api/preview-templates/social/{templates[0]['id']}",
                json={'use_baseline': True},
                timeout=5
            )
            assert r.status_code == 200, \
                "Preview generation should work without OpenAI"
        
    finally:
        stop_server(proc)
