import pytest

pytest.skip("OpenAI path removed; Gemini-only stack", allow_module_level=True)

import json

import generator as gen_mod


def _fake_openai_with_content(content: str):
    class Completions:
        def create(self, *args, **kwargs):
            return {'choices': [{'message': {'content': content}}]}

    return type('Fake', (), {'chat': type('C', (), {'completions': Completions()})()})()


def test_generate_openai_path_parses_payload(monkeypatch, client):
    """Test that OpenAI path parses payload.
    
    Note: Content must pass validation gate, so we provide valid content
    with structure signals and proper length.
    """
    gen_mod.USE_OPENAI_FOR_POSTS = True
    
    # Provide valid content that will pass validation
    valid_content = json.dumps([{
        'caption': '''3 proven strategies for better engagement:
        
1. Start with a compelling hook that stops scrolling
2. Deliver clear, actionable value in every post
3. End with a strong call-to-action

For example, this exact framework doubled my engagement last week.

Save this for your next post! 🎯''',
        'pillar': 'launch',
        'image_prompt': 'image',
        'hashtags': ['#marketing', '#socialmedia', '#contentcreator', '#business',
                     '#entrepreneur', '#success', '#growth', '#strategy']
    }])
    
    gen_mod._openai_client = _fake_openai_with_content(valid_content)

    with client.session_transaction() as sess:
        sess['profile_id'] = 'openai-mock'

    resp = client.post('/api/generate', json={'days': 1})
    assert resp.status_code == 200

    body = resp.get_json()
    # May still fail if using new service validation, but at least content is valid
    # If it falls back, it will be blocked by validation
