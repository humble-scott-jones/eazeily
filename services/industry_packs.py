import os
import json

class IndustryPackLoader:
    def __init__(self, packs_dir='data/packs'):
        self.packs_dir = packs_dir

    def get_defaults(self, industry_slug):
        """
        Loads the specific JSON pack for an industry or falls back to General.
        """
        filename = f"{industry_slug.lower()}.json"
        filepath = os.path.join(self.packs_dir, filename)
        
        if not os.path.exists(filepath):
            filepath = os.path.join(self.packs_dir, 'general.json')
            
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading pack {filepath}: {e}")
            return {}
