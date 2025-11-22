import app


class _DummyCompletions:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        # minimal response structure consumed by _extract_choice_content
        return type('Resp', (), {'choices': [{'message': {'content': '[]'}}]})


class _DummyChat:
    def __init__(self):
        self.completions = _DummyCompletions()


class _DummyClient:
    def __init__(self):
        self.chat = _DummyChat()


def test_image_generation_prompt_includes_voice_profile(monkeypatch):
    client = _DummyClient()
    monkeypatch.setattr(app, 'openai_client', client)
    monkeypatch.setattr(app, 'USE_OPENAI', True)

    spec = {
        'image_data_url': 'data:image/png;base64,abc123',
        'platforms': ['instagram'],
        'tone': 'friendly',
        'industry': 'Fitness',
        'company': 'Acme Fit',
        'brand_keywords': ['coaching'],
        'voice_profile': {
            'include_phrases': ['let’s move', 'we got you'],
            'avoid_phrases': ['synergy'],
            'example_lines': ['We got you—small steps daily add up.'],
            'avg_length': 24.5,
        }
    }

    app._generate_posts_from_image(spec)
    text_block = client.chat.completions.kwargs['messages'][1]['content'][0]['text']

    assert 'voice profile' in text_block.lower()
    assert 'include_phrases' in text_block
    assert 'avoid_phrases' in text_block
    assert 'examples' in text_block
