# -*- coding: utf-8 -*-
"""
SysCRED Configuration
=====================
Configuration centralisée pour le système de vérification de crédibilité.

Usage:
    from syscred.config import Config
    
    # Accéder aux paramètres
    config = Config()
    port = config.PORT
    
    # Ou avec variables d'environnement
    # export SYSCRED_GOOGLE_API_KEY=your_key
    # export SYSCRED_PORT=8080

(c) Dominique S. Loyer - PhD Thesis Prototype
"""

import os
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

# Charger les variables depuis .env
# Charger les variables depuis .env (Project Root)
# Path: .../systemFactChecking/02_Code/syscred/config.py
# Root .env is at .../systemFactChecking/.env (3 levels up)
current_path = Path(__file__).resolve()
env_path = current_path.parent.parent.parent / '.env'

if not env_path.exists():
    print(f"[Config] WARNING: .env not found at {env_path}")
    # Try alternate location (sometimes CWD matters)
    env_path = Path.cwd().parent / '.env'
    
load_dotenv(dotenv_path=env_path)
print(f"[Config] Loading .env from {env_path}")
print(f"[Config] SYSCRED_GOOGLE_API_KEY loaded: {'Yes' if os.environ.get('SYSCRED_GOOGLE_API_KEY') else 'No'}")



class Config:
    """
    Configuration centralisée pour SysCRED.
    
    Les valeurs peuvent être override par des variables d'environnement
    préfixées par SYSCRED_.
    """
    
    # === Chemins ===
    BASE_DIR = Path(__file__).parent.parent
    ONTOLOGY_BASE_PATH = BASE_DIR / "sysCRED_onto26avrtil.ttl"
    ONTOLOGY_DATA_PATH = BASE_DIR / "ontology" / "sysCRED_data.ttl"
    
    # === Serveur Flask ===
    HOST = os.getenv("SYSCRED_HOST", "0.0.0.0")
    PORT = int(os.getenv("SYSCRED_PORT", "5000"))
    DEBUG = os.getenv("SYSCRED_DEBUG", "true").lower() == "true"
    
    # === API Keys ===
    GOOGLE_FACT_CHECK_API_KEY = os.getenv("SYSCRED_GOOGLE_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL") # [NEW] Read DB URL from env
    
    # === Modèles ML ===
    LOAD_ML_MODELS = os.getenv("SYSCRED_LOAD_ML", "true").lower() == "true"
    SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
    NER_MODEL = "dbmdz/bert-large-cased-finetuned-conll03-english"
    
    # === Timeouts ===
    WEB_FETCH_TIMEOUT = int(os.getenv("SYSCRED_TIMEOUT", "10"))
    
    # === Pondération des scores ===
    SCORE_WEIGHTS = {
        'source_reputation': 0.25,
        'domain_age': 0.10,
        'sentiment_neutrality': 0.15,
        'entity_presence': 0.15,
        'coherence': 0.15,
        'fact_check': 0.20
    }
    
    # === Seuils de crédibilité ===
    CREDIBILITY_THRESHOLDS = {
        'HIGH': 0.7,
        'MEDIUM': 0.4,
        'LOW': 0.0
    }
    
    # === Base de données de réputation ===
    # Les sources peuvent être étendues ou chargées d'un fichier externe
    SOURCE_REPUTATIONS: Dict[str, str] = {
        # === HAUTE CRÉDIBILITÉ ===
        # Médias internationaux
        'lemonde.fr': 'High',
        'nytimes.com': 'High',
        'reuters.com': 'High',
        'bbc.com': 'High',
        'bbc.co.uk': 'High',
        'theguardian.com': 'High',
        'apnews.com': 'High',
        'afp.com': 'High',
        'france24.com': 'High',
        
        # Médias canadiens
        'cbc.ca': 'High',
        'radio-canada.ca': 'High',
        'lapresse.ca': 'High',
        'ledevoir.com': 'High',
        'theglobeandmail.com': 'High',
        
        # Sources académiques
        'nature.com': 'High',
        'sciencedirect.com': 'High',
        'scholar.google.com': 'High',
        'pubmed.ncbi.nlm.nih.gov': 'High',
        'jstor.org': 'High',
        'springer.com': 'High',
        'ieee.org': 'High',
        'acm.org': 'High',
        'arxiv.org': 'High',
        
        # Fact-checkers
        'factcheck.org': 'High',
        'snopes.com': 'High',
        'politifact.com': 'High',
        'fullfact.org': 'High',
        'checknews.fr': 'High',
        
        # Institutions
        'who.int': 'High',
        'un.org': 'High',
        'europa.eu': 'High',
        'canada.ca': 'High',
        'gouv.fr': 'High',
        'gouv.qc.ca': 'High',
        
        # === CRÉDIBILITÉ MOYENNE ===
        'wikipedia.org': 'Medium',
        'medium.com': 'Medium',
        'huffpost.com': 'Medium',
        'buzzfeed.com': 'Medium',
        'vice.com': 'Medium',
        'slate.com': 'Medium',
        'theconversation.com': 'Medium',
        
        # === BASSE CRÉDIBILITÉ ===
        'infowars.com': 'Low',
        'naturalnews.com': 'Low',
        'breitbart.com': 'Low',
        'dailystormer.su': 'Low',
        'beforeitsnews.com': 'Low',
        'worldtruth.tv': 'Low',
        'yournewswire.com': 'Low',
    }
    
    # === Patterns de mésinformation ===
    MISINFORMATION_KEYWORDS = [
        'conspiracy', 'hoax', 'fake news', 'miracle cure', 
        "they don't want you to know", 'mainstream media lies',
        'deep state', 'plandemic', 'wake up sheeple',
        'big pharma cover-up', 'government conspiracy',
        'censored truth', 'what they hide'
    ]
    
    @classmethod
    def load_external_reputations(cls, filepath: str) -> None:
        """
        Charger des réputations supplémentaires depuis un fichier JSON.
        
        Args:
            filepath: Chemin vers le fichier JSON avec format:
                      {"domain.com": "High", "autre.com": "Low"}
        """
        import json
        try:
            with open(filepath, 'r') as f:
                external_reps = json.load(f)
                cls.SOURCE_REPUTATIONS.update(external_reps)
                print(f"[Config] Loaded {len(external_reps)} external reputations")
        except Exception as e:
            print(f"[Config] Could not load external reputations: {e}")
    
    @classmethod
    def update_weights(cls, new_weights: Dict[str, float]) -> None:
        """
        Mettre à jour les pondérations des scores.
        
        Args:
            new_weights: Dictionnaire avec les nouvelles pondérations
        """
        cls.SCORE_WEIGHTS.update(new_weights)
        # Normaliser pour que la somme = 1
        total = sum(cls.SCORE_WEIGHTS.values())
        cls.SCORE_WEIGHTS = {k: v/total for k, v in cls.SCORE_WEIGHTS.items()}
        print(f"[Config] Updated weights: {cls.SCORE_WEIGHTS}")
    
    @classmethod
    def to_dict(cls) -> Dict:
        """Exporter la configuration actuelle en dictionnaire."""
        return {
            'host': cls.HOST,
            'port': cls.PORT,
            'debug': cls.DEBUG,
            'google_api_configured': cls.GOOGLE_FACT_CHECK_API_KEY is not None,
            'ml_models_enabled': cls.LOAD_ML_MODELS,
            'score_weights': cls.SCORE_WEIGHTS,
            'known_sources_count': len(cls.SOURCE_REPUTATIONS),
            'ontology_base': str(cls.ONTOLOGY_BASE_PATH),
            'ontology_data': str(cls.ONTOLOGY_DATA_PATH),
        }
    
    @classmethod
    def print_config(cls) -> None:
        """Afficher la configuration actuelle."""
        print("=" * 50)
        print("SysCRED Configuration")
        print("=" * 50)
        for key, value in cls.to_dict().items():
            print(f"  {key}: {value}")
        print("=" * 50)


# === Configuration par environnement ===

class DevelopmentConfig(Config):
    """Configuration pour développement local."""
    DEBUG = True
    LOAD_ML_MODELS = True


class ProductionConfig(Config):
    """Configuration pour production."""
    DEBUG = False
    LOAD_ML_MODELS = True
    HOST = "0.0.0.0"


class TestingConfig(Config):
    """Configuration pour tests."""
    DEBUG = True
    LOAD_ML_MODELS = False  # Plus rapide pour les tests
    WEB_FETCH_TIMEOUT = 5


# Sélection automatique de la configuration
def get_config() -> Config:
    """
    Retourne la configuration appropriée selon l'environnement.
    
    Variable d'environnement: SYSCRED_ENV (development, production, testing)
    """
    env = os.getenv("SYSCRED_ENV", "development").lower()
    
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
    }
    
    return configs.get(env, DevelopmentConfig)


# Instance par défaut
config = get_config()


if __name__ == "__main__":
    # Test de la configuration
    config.print_config()
    
    print("\n=== Source Reputations Sample ===")
    for domain, rep in list(config.SOURCE_REPUTATIONS.items())[:10]:
        print(f"  {domain}: {rep}")
