#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Named Entity Recognition (NER) Analyzer for SysCRED
====================================================
Extracts named entities from text using spaCy.

Entities detected:
- PER: Persons (Donald Trump, Emmanuel Macron)
- ORG: Organizations (FBI, UN, Google)
- LOC: Locations (Paris, Capitol)
- DATE: Dates (January 6, 2021)
- MONEY: Amounts ($10 million)
- EVENT: Events (insurrection, election)
"""

from typing import Dict, List, Any, Optional
import logging

# Try to import spaCy
try:
    import spacy
    from spacy.language import Language
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    spacy = None

logger = logging.getLogger(__name__)


class NERAnalyzer:
    """
    Named Entity Recognition analyzer using spaCy.
    
    Supports French (fr_core_news_md) and English (en_core_web_md).
    Falls back to heuristic extraction if spaCy is not available.
    """
    
    # Entity type mappings for display
    ENTITY_LABELS = {
        'PER': {'fr': 'Personne', 'en': 'Person', 'emoji': '👤'},
        'PERSON': {'fr': 'Personne', 'en': 'Person', 'emoji': '👤'},
        'ORG': {'fr': 'Organisation', 'en': 'Organization', 'emoji': '🏢'},
        'LOC': {'fr': 'Lieu', 'en': 'Location', 'emoji': '📍'},
        'GPE': {'fr': 'Lieu géopolitique', 'en': 'Geopolitical', 'emoji': '🌍'},
        'DATE': {'fr': 'Date', 'en': 'Date', 'emoji': '📅'},
        'TIME': {'fr': 'Heure', 'en': 'Time', 'emoji': '⏰'},
        'MONEY': {'fr': 'Montant', 'en': 'Money', 'emoji': '💰'},
        'PERCENT': {'fr': 'Pourcentage', 'en': 'Percent', 'emoji': '📊'},
        'EVENT': {'fr': 'Événement', 'en': 'Event', 'emoji': '📰'},
        'PRODUCT': {'fr': 'Produit', 'en': 'Product', 'emoji': '📦'},
        'LAW': {'fr': 'Loi', 'en': 'Law', 'emoji': '⚖️'},
        'NORP': {'fr': 'Groupe', 'en': 'Group', 'emoji': '👥'},
        'MISC': {'fr': 'Divers', 'en': 'Miscellaneous', 'emoji': '🔖'},
    }
    
    def __init__(self, model_name: str = "fr_core_news_md", fallback: bool = True):
        """
        Initialize NER analyzer.
        
        Args:
            model_name: spaCy model to load (fr_core_news_md, en_core_web_md)
            fallback: If True, use heuristics when spaCy unavailable
        """
        self.model_name = model_name
        self.fallback = fallback
        self.nlp = None
        self.use_heuristics = False
        
        if HAS_SPACY:
            try:
                self.nlp = spacy.load(model_name)
                logger.info(f"[NER] Loaded spaCy model: {model_name}")
            except OSError as e:
                logger.warning(f"[NER] Could not load model {model_name}: {e}")
                if fallback:
                    self.use_heuristics = True
                    logger.info("[NER] Using heuristic entity extraction")
        else:
            if fallback:
                self.use_heuristics = True
                logger.info("[NER] spaCy not installed. Using heuristic extraction")
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract named entities from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary mapping entity types to lists of entities
            Each entity has: text, start, end, label, label_display, emoji, confidence
        """
        if not text or len(text.strip()) == 0:
            return {}
        
        if self.nlp:
            return self._extract_with_spacy(text)
        elif self.use_heuristics:
            return self._extract_with_heuristics(text)
        else:
            return {}
    
    def _extract_with_spacy(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities using spaCy NLP."""
        doc = self.nlp(text)
        entities: Dict[str, List[Dict[str, Any]]] = {}
        
        for ent in doc.ents:
            label = ent.label_
            
            # Get display info
            label_info = self.ENTITY_LABELS.get(label, {
                'fr': label, 
                'en': label, 
                'emoji': '🔖'
            })
            
            entity_data = {
                'text': ent.text,
                'start': ent.start_char,
                'end': ent.end_char,
                'label': label,
                'label_display': label_info.get('fr', label),
                'emoji': label_info.get('emoji', '🔖'),
                'confidence': 0.85  # spaCy doesn't provide confidence by default
            }
            
            if label not in entities:
                entities[label] = []
            
            # Avoid duplicates
            if not any(e['text'].lower() == entity_data['text'].lower() for e in entities[label]):
                entities[label].append(entity_data)
        
        return entities
    
    def _extract_with_heuristics(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fallback heuristic entity extraction.
        Uses pattern matching for common entities.
        """
        import re
        entities: Dict[str, List[Dict[str, Any]]] = {}
        
        # Common patterns
        patterns = {
            'PER': [
                # Known political figures
                r'\b(Donald Trump|Joe Biden|Emmanuel Macron|Hillary Clinton|Barack Obama|'
                r'Vladimir Putin|Angela Merkel|Justin Trudeau|Boris Johnson)\b',
            ],
            'ORG': [
                r'\b(FBI|CIA|NSA|ONU|NATO|OTAN|Google|Facebook|Twitter|Meta|'
                r'Amazon|Microsoft|Apple|CNN|BBC|Le Monde|New York Times|'
                r'Parti Républicain|Parti Démocrate|Republican Party|Democratic Party)\b',
            ],
            'LOC': [
                r'\b(Capitol|White House|Maison Blanche|Kremlin|Élysée|Pentagon|'
                r'New York|Washington|Paris|Londres|Moscou|Berlin|Beijing)\b',
            ],
            'DATE': [
                r'\b(\d{1,2}\s+(janvier|février|mars|avril|mai|juin|juillet|août|'
                r'septembre|octobre|novembre|décembre)\s+\d{4})\b',
                r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b',
                r'\b(January|February|March|April|May|June|July|August|'
                r'September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            ],
            'MONEY': [
                r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|trillion))?',
                r'[\d,]+(?:\.\d{2})?\s*(?:dollars?|euros?|€|\$)',
                r'[\d,]+\s*(?:million|milliard)s?\s*(?:de\s+)?(?:dollars?|euros?)',
            ],
            'PERCENT': [
                r'\b\d+(?:\.\d+)?%',
                r'\b\d+(?:\.\d+)?\s*pour\s*cent',
                r'\b\d+(?:\.\d+)?\s*percent',
            ],
        }
        
        for label, pattern_list in patterns.items():
            label_info = self.ENTITY_LABELS.get(label, {'fr': label, 'emoji': '🔖'})
            
            for pattern in pattern_list:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entity_data = {
                        'text': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'label': label,
                        'label_display': label_info.get('fr', label),
                        'emoji': label_info.get('emoji', '🔖'),
                        'confidence': 0.70  # Lower confidence for heuristics
                    }
                    
                    if label not in entities:
                        entities[label] = []
                    
                    # Avoid duplicates
                    if not any(e['text'].lower() == entity_data['text'].lower() 
                              for e in entities[label]):
                        entities[label].append(entity_data)
        
        return entities
    
    def get_entity_summary(self, entities: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Generate a human-readable summary of extracted entities.
        
        Args:
            entities: Dictionary of entities from extract_entities()
            
        Returns:
            Formatted string summary
        """
        if not entities:
            return "Aucune entité nommée détectée."
        
        lines = []
        for label, ent_list in entities.items():
            label_info = self.ENTITY_LABELS.get(label, {'fr': label, 'emoji': '🔖'})
            emoji = label_info.get('emoji', '🔖')
            label_display = label_info.get('fr', label)
            
            entity_texts = [e['text'] for e in ent_list[:5]]  # Limit to 5
            lines.append(f"{emoji} {label_display}: {', '.join(entity_texts)}")
        
        return "\n".join(lines)
    
    def to_frontend_format(self, entities: Dict[str, List[Dict[str, Any]]]) -> List[Dict]:
        """
        Convert entities to frontend-friendly format.
        
        Returns:
            List of entities with all info for display
        """
        result = []
        for label, ent_list in entities.items():
            for ent in ent_list:
                result.append({
                    'text': ent['text'],
                    'type': ent['label'],
                    'type_display': ent.get('label_display', ent['label']),
                    'emoji': ent.get('emoji', '🔖'),
                    'confidence': ent.get('confidence', 0.5),
                    'confidence_pct': f"{int(ent.get('confidence', 0.5) * 100)}%"
                })
        
        # Sort by confidence
        result.sort(key=lambda x: x['confidence'], reverse=True)
        return result


# Singleton instance for easy import
_ner_analyzer: Optional[NERAnalyzer] = None


def get_ner_analyzer(model_name: str = "fr_core_news_md") -> NERAnalyzer:
    """Get or create singleton NER analyzer instance."""
    global _ner_analyzer
    if _ner_analyzer is None:
        _ner_analyzer = NERAnalyzer(model_name=model_name, fallback=True)
    return _ner_analyzer


# Quick test
if __name__ == "__main__":
    analyzer = NERAnalyzer(fallback=True)
    
    test_text = """
    Donald Trump a affirmé que l'insurrection du 6 janvier 2021 au Capitol n'est jamais arrivée.
    Le FBI enquête sur les événements. Le président Joe Biden a condamné ces déclarations à Washington.
    Les dégâts sont estimés à 30 millions de dollars.
    """
    
    entities = analyzer.extract_entities(test_text)
    print("=== Entités détectées ===")
    print(analyzer.get_entity_summary(entities))
    print("\n=== Format Frontend ===")
    for e in analyzer.to_frontend_format(entities):
        print(f"  {e['emoji']} {e['text']} ({e['type_display']}, {e['confidence_pct']})")
