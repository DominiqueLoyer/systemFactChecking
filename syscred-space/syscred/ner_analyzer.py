# -*- coding: utf-8 -*-
"""
NER Analyzer Module - SysCRED
==============================
Named Entity Recognition for fact-checking enhancement.

Extracts: PERSON, ORG, GPE, DATE, MISC entities

(c) Dominique S. Loyer - PhD Thesis Prototype
"""

import os

# Check for spaCy
try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    print("[NER] spaCy not installed. NER disabled.")


class NERAnalyzer:
    """
    Named Entity Recognition using spaCy.
    
    Supports:
    - French (fr_core_news_md)
    - English (en_core_web_sm)
    """
    
    # Entity type mapping with icons
    ENTITY_ICONS = {
        'PERSON': '👤',
        'PER': '👤',
        'ORG': '🏢',
        'GPE': '📍',
        'LOC': '📍',
        'DATE': '📅',
        'TIME': '🕐',
        'MONEY': '💰',
        'MISC': '🏷️',
        'NORP': '👥',
        'FAC': '🏛️',
        'PRODUCT': '📦',
        'EVENT': '🎉',
        'WORK_OF_ART': '🎨',
        'LAW': '⚖️',
        'LANGUAGE': '🗣️',
    }
    
    def __init__(self, language: str = 'en'):
        """
        Initialize NER analyzer.
        
        Args:
            language: 'en' or 'fr'
        """
        self.language = language
        self.nlp = None
        self.enabled = False
        
        if HAS_SPACY:
            self._load_model()
    
    def _load_model(self):
        """Load the appropriate spaCy model."""
        models = {
            'en': ['en_core_web_sm', 'en_core_web_md'],
            'fr': ['fr_core_news_md', 'fr_core_news_sm']
        }
        
        for model_name in models.get(self.language, models['en']):
            try:
                self.nlp = spacy.load(model_name)
                self.enabled = True
                print(f"[NER] Loaded model: {model_name}")
                break
            except OSError:
                continue
        
        if not self.enabled:
            print(f"[NER] No model found for language: {self.language}")
    
    def extract_entities(self, text: str) -> dict:
        """
        Extract named entities from text.
        
        Returns:
            {
                'entities': [
                    {'text': 'Emmanuel Macron', 'type': 'PERSON', 'icon': '👤'},
                    ...
                ],
                'summary': {
                    'PERSON': ['Emmanuel Macron'],
                    'ORG': ['UQAM', 'Google'],
                    ...
                }
            }
        """
        if not self.enabled or not text:
            return {'entities': [], 'summary': {}}
        
        doc = self.nlp(text)
        
        entities = []
        summary = {}
        seen = set()
        
        for ent in doc.ents:
            # Avoid duplicates
            key = (ent.text.lower(), ent.label_)
            if key in seen:
                continue
            seen.add(key)
            
            entity = {
                'text': ent.text,
                'type': ent.label_,
                'icon': self.ENTITY_ICONS.get(ent.label_, '🏷️'),
                'start': ent.start_char,
                'end': ent.end_char
            }
            entities.append(entity)
            
            # Group by type
            if ent.label_ not in summary:
                summary[ent.label_] = []
            summary[ent.label_].append(ent.text)
        
        return {
            'entities': entities,
            'summary': summary,
            'count': len(entities)
        }
    
    def analyze_for_factcheck(self, text: str) -> dict:
        """
        Analyze text for fact-checking relevance.
        
        Returns entities with credibility hints.
        """
        result = self.extract_entities(text)
        
        # Add fact-checking hints
        hints = []
        
        for ent in result.get('entities', []):
            if ent['type'] in ['PERSON', 'PER']:
                hints.append(f"Verify claims about {ent['text']}")
            elif ent['type'] == 'ORG':
                hints.append(f"Check {ent['text']} official sources")
            elif ent['type'] in ['GPE', 'LOC']:
                hints.append(f"Verify location: {ent['text']}")
            elif ent['type'] == 'DATE':
                hints.append(f"Confirm date: {ent['text']}")
        
        result['fact_check_hints'] = hints[:5]  # Top 5 hints
        return result


# Singleton instance
_analyzer = None

def get_analyzer(language: str = 'en') -> NERAnalyzer:
    """Get or create the NER analyzer singleton."""
    global _analyzer
    if _analyzer is None:
        _analyzer = NERAnalyzer(language)
    return _analyzer


# --- Testing ---
if __name__ == "__main__":
    print("=" * 60)
    print("SysCRED NER Analyzer - Test")
    print("=" * 60)
    
    analyzer = NERAnalyzer('en')
    
    test_text = """
    Emmanuel Macron announced today that France will invest €500 million 
    in AI research. The announcement was made at the UQAM in Montreal, Canada 
    on February 8, 2026. Google and Microsoft also confirmed their participation.
    """
    
    result = analyzer.analyze_for_factcheck(test_text)
    
    print("\n--- Entities Found ---")
    for ent in result['entities']:
        print(f"  {ent['icon']} {ent['text']} ({ent['type']})")
    
    print("\n--- Fact-Check Hints ---")
    for hint in result.get('fact_check_hints', []):
        print(f"  • {hint}")
    
    print("\n" + "=" * 60)
