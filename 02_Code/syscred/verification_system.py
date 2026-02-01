# -*- coding: utf-8 -*-
"""
Verification System Module - SysCRED v2.0
==========================================
Main credibility verification system with real API integration.
Refactored from sys-cred-Python-27avril2025.py

(c) Dominique S. Loyer - PhD Thesis Prototype
Citation Key: loyerModelingHybridSystem2025
"""

import re
import json
import datetime
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

# Transformers and ML
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import numpy as np
    import torch
    from lime.lime_text import LimeTextExplainer
    HAS_ML = True
except ImportError:
    HAS_ML = False
    print("Warning: ML libraries not fully installed. Run: pip install transformers torch lime numpy")

try:
    from sentence_transformers import SentenceTransformer, util
    HAS_SBERT = True
except ImportError:
    HAS_SBERT = False
    print("Warning: sentence-transformers not installed. Semantic coherence will use heuristics.")

# Local imports
from syscred.api_clients import ExternalAPIClients, WebContent, ExternalData
from syscred.ontology_manager import OntologyManager
from syscred.seo_analyzer import SEOAnalyzer
from syscred.graph_rag import GraphRAG  # [NEW] GraphRAG


class CredibilityVerificationSystem:
    """
    Système neuro-symbolique de vérification de crédibilité.
    
    Combine:
    - Analyse basée sur des règles (symbolique, transparent)
    - Analyse NLP/IA (apprentissage automatique)
    - Ontologie OWL pour la traçabilité
    - APIs externes pour les données réelles
    """
    
    def __init__(
        self, 
        google_api_key: Optional[str] = None,
        ontology_base_path: Optional[str] = None,
        ontology_data_path: Optional[str] = None,
        load_ml_models: bool = True
    ):
        """
        Initialize the credibility verification system.
        
        Args:
            google_api_key: API key for Google Fact Check (optional)
            ontology_base_path: Path to base ontology TTL file
            ontology_data_path: Path to store accumulated data
            load_ml_models: Whether to load ML models (disable for testing)
        """
        print("[SysCRED] Initializing Credibility Verification System v2.0...")
        
        # Initialize API clients
        self.api_clients = ExternalAPIClients(google_api_key=google_api_key)
        print("[SysCRED] API clients initialized")
        
        # Initialize ontology manager
        self.ontology_manager = None
        if ontology_base_path or ontology_data_path:
            try:
                self.ontology_manager = OntologyManager(
                    base_ontology_path=ontology_base_path,
                    data_path=ontology_data_path
                )
                self.graph_rag = GraphRAG(self.ontology_manager) # [NEW] Init GraphRAG
                print("[SysCRED] Ontology manager & GraphRAG initialized")
            except Exception as e:
                print(f"[SysCRED] Ontology manager disabled: {e}")
                self.graph_rag = None
        else:
             self.graph_rag = None
        
        # Initialize ML models
        self.sentiment_pipeline = None
        self.ner_pipeline = None
        self.bias_tokenizer = None
        self.bias_model = None
        self.coherence_model = None
        self.explainer = None
        
        if load_ml_models and HAS_ML:
            self._load_ml_models()
        
        # Weights for score calculation (configurable)
        # Weights for score calculation (Loaded from Config)
        self.weights = config.Config.SCORE_WEIGHTS
        print(f"[SysCRED] Using weights: {self.weights}")
        
        print("[SysCRED] System ready!")
    
    def _load_ml_models(self):
        """Load ML models for NLP analysis."""
        print("[SysCRED] Loading ML models (this may take a moment)...")
        
        try:
            # Sentiment analysis
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis", 
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            print("[SysCRED] ✓ Sentiment model loaded")
        except Exception as e:
            print(f"[SysCRED] ✗ Sentiment model failed: {e}")
        
        try:
            # NER pipeline
            self.ner_pipeline = pipeline("ner", grouped_entities=True)
            print("[SysCRED] ✓ NER model loaded")
        except Exception as e:
            print(f"[SysCRED] ✗ NER model failed: {e}")
        
        try:
            # Bias detection - Specialized model
            # Using 'd4data/bias-detection-model' or fallback to generic
            bias_model_name = "d4data/bias-detection-model"
            self.bias_tokenizer = AutoTokenizer.from_pretrained(bias_model_name)
            self.bias_model = AutoModelForSequenceClassification.from_pretrained(bias_model_name)
            print("[SysCRED] ✓ Bias model loaded (d4data)")
        except Exception as e:
            print(f"[SysCRED] ✗ Bias model failed: {e}. Using heuristics.")

        try:
            # Semantic Coherence
            if HAS_SBERT:
                self.coherence_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("[SysCRED] ✓ Coherence model loaded (SBERT)")
        except Exception as e:
            print(f"[SysCRED] ✗ Coherence model failed: {e}")
        
        try:
            # LIME explainer
            self.explainer = LimeTextExplainer(class_names=['NEGATIVE', 'POSITIVE'])
            print("[SysCRED] ✓ LIME explainer loaded")
        except Exception as e:
            print(f"[SysCRED] ✗ LIME explainer failed: {e}")
    
    def is_url(self, text: str) -> bool:
        """Check if a string is a valid URL."""
        try:
            result = urlparse(text)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False
    
    def preprocess(self, text: str) -> str:
        """Clean and normalize text for analysis."""
        if not isinstance(text, str):
            return ""
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Keep basic punctuation
        text = re.sub(r'[^\w\s\.\?,!]', '', text)
        
        return text.lower().strip()
    
    def rule_based_analysis(self, text: str, external_data: ExternalData) -> Dict[str, Any]:
        """
        Perform rule-based analysis using symbolic reasoning.
        
        Args:
            text: Preprocessed text to analyze
            external_data: Data from external APIs
            
        Returns:
            Dictionary with rule-based analysis results
        """
        results = {
            'linguistic_markers': {},
            'source_analysis': {},
            'timeliness_flags': [],
            'fact_checking': []
        }
        
        # 1. Linguistic markers
        sensational_words = [
            'shocking', 'revealed', 'conspiracy', 'amazing', 'secret',
            'breakthrough', 'miracle', 'unbelievable', 'exclusive', 'urgent'
        ]
        certainty_words = [
            'verified', 'authentic', 'credible', 'proven', 'fact',
            'confirmed', 'official', 'legitimate', 'established'
        ]
        doubt_words = [
            'hoax', 'false', 'fake', 'unproven', 'rumor', 'allegedly',
            'claim', 'debunked', 'misleading', 'disputed'
        ]
        
        text_lower = text.lower()
        results['linguistic_markers']['sensationalism'] = sum(
            1 for word in sensational_words if word in text_lower
        )
        results['linguistic_markers']['certainty'] = sum(
            1 for word in certainty_words if word in text_lower
        )
        results['linguistic_markers']['doubt'] = sum(
            1 for word in doubt_words if word in text_lower
        )
        
        # 2. Source analysis from external data
        results['source_analysis']['reputation'] = external_data.source_reputation
        results['source_analysis']['domain_age_days'] = external_data.domain_age_days
        
        if external_data.domain_info:
            results['source_analysis']['registrar'] = external_data.domain_info.registrar
            results['source_analysis']['domain'] = external_data.domain_info.domain
        
        # 3. Timeliness flags
        if external_data.domain_age_days is not None:
            if external_data.domain_age_days < 180:
                results['timeliness_flags'].append('Source domain is relatively new (<6 months)')
            elif external_data.domain_age_days < 365:
                results['timeliness_flags'].append('Source domain is less than 1 year old')
        
        # 4. Fact checking results
        for fc in external_data.fact_checks:
            results['fact_checking'].append({
                'claim': fc.claim,
                'rating': fc.rating,
                'publisher': fc.publisher,
                'url': fc.url
            })
        
        return results
    
    def nlp_analysis(self, text: str) -> Dict[str, Any]:
        """
        Perform NLP-based analysis using ML models.
        
        Args:
            text: Preprocessed text to analyze
            
        Returns:
            Dictionary with NLP analysis results
        """
        results = {
            'sentiment': None,
            'sentiment_explanation': None,
            'bias_analysis': {'score': None, 'label': 'Unavailable'},
            'named_entities': [],
            'coherence_score': None
        }
        
        if not text:
            results['sentiment'] = {'label': 'Neutral', 'score': 0.5}
            return results
        
        # 1. Sentiment analysis with LIME explanation
        if self.sentiment_pipeline:
            try:
                main_pred = self.sentiment_pipeline(text[:512])[0]
                results['sentiment'] = main_pred
                
                if self.explainer:
                    def predict_proba(texts):
                        if isinstance(texts, str):
                            texts = [texts]
                        predictions = self.sentiment_pipeline(list(texts))
                        probs = []
                        for pred in predictions:
                            if pred['label'] == 'POSITIVE':
                                probs.append([1 - pred['score'], pred['score']])
                            else:
                                probs.append([pred['score'], 1 - pred['score']])
                        return np.array(probs)
                    
                    explanation = self.explainer.explain_instance(
                        text[:512], predict_proba, num_features=6
                    )
                    results['sentiment_explanation'] = explanation.as_list()
            except Exception as e:
                print(f"[NLP] Sentiment error: {e}")
                results['sentiment'] = {'label': 'Error', 'score': 0.0}
        
        # 2. Bias analysis
        results['bias_analysis'] = self._analyze_bias(text)
        
        # 3. Named Entity Recognition
        if self.ner_pipeline:
            try:
                entities = self.ner_pipeline(text[:512])
                results['named_entities'] = entities
            except Exception as e:
                print(f"[NLP] NER error: {e}")
        
        # 4. Semantic Coherence
        results['coherence_score'] = self._calculate_coherence(text)
        
        return results

    def _analyze_bias(self, text: str) -> Dict[str, Any]:
        """Analyze text for bias using ML or heuristics."""
        # Method 1: ML Model
        if self.bias_model and self.bias_tokenizer:
            try:
                inputs = self.bias_tokenizer(
                    text[:512], return_tensors="pt", 
                    truncation=True, max_length=512, padding=True
                )
                with torch.no_grad():
                    logits = self.bias_model(**inputs).logits
                probs = torch.softmax(logits, dim=1)[0]
                # Label mapping depends on model, usually [Non-biased, Biased]
                bias_score = probs[1].item() 
                
                label = " biased" if bias_score > 0.5 else "Non-biased"
                return {'score': bias_score, 'label': label, 'method': 'ML (d4data)'}
            except Exception as e:
                print(f"[NLP] ML Bias error: {e}")
        
        # Method 2: Heuristics
        biased_words = [
            'radical', 'extremist', 'disgraceful', 'shameful', 'corrupt', 
            'insane', 'idiot', 'disaster', 'propaganda', 'dictator',
            'puppet', 'regime', 'tyrant', 'treason', 'traitor'
        ]
        text_lower = text.lower()
        count = sum(1 for w in biased_words if w in text_lower)
        score = min(1.0, count * 0.15)
        label = "Potentially Biased" if score > 0.3 else "Neutral"
        return {'score': score, 'label': label, 'method': 'Heuristic'}

    def _calculate_coherence(self, text: str) -> float:
        """Calculate semantic coherence score."""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.split()) > 3]
        
        if len(sentences) < 2:
            return 0.7  # Default to neutral/good for short text, not perfect 1.0
            
        # Method 1: SBERT Semantic Similarity
        if self.coherence_model and HAS_SBERT:
            try:
                embeddings = self.coherence_model.encode(sentences[:10]) # Limit to 10
                sims = []
                for i in range(len(embeddings) - 1):
                    sim = util.pytorch_cos_sim(embeddings[i], embeddings[i+1])
                    sims.append(sim.item())
                return sum(sims) / len(sims) if sims else 0.5
            except Exception as e:
                print(f"[NLP] SBERT error: {e}")
        
        # Method 2: Heuristic (Sentence Length Variance & Repetition)
        lengths = [len(s.split()) for s in sentences]
        avg_len = sum(lengths) / len(lengths)
        variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
        
        # High variance suggests simpler/choppier writing usually
        score = 0.8
        if variance > 100: score -= 0.2
        if avg_len < 5: score -= 0.2
        
        return max(0.0, score)
    
    def calculate_overall_score(
        self, 
        rule_results: Dict, 
        nlp_results: Dict
    ) -> float:
        """
        Calculate overall credibility score based on User-Defined Metrics.
        """
        score = 0.5  # Start neutral
        adjustments = 0.0
        total_weight_used = 0.0
        
        # 1. Source Reputation (25%)
        w_rep = self.weights.get('source_reputation', 0.25)
        reputation = rule_results['source_analysis'].get('reputation', 'Unknown')
        if reputation != 'Unknown' and "N/A" not in reputation:
            if reputation == 'High':
                adjustments += w_rep * 1.0 # Full boost
            elif reputation == 'Low':
                adjustments -= w_rep * 1.0 # Full penalty
            elif reputation == 'Medium':
                adjustments += w_rep * 0.2 # Slight boost
            total_weight_used += w_rep
        
        # 2. Domain Age (10%)
        w_age = self.weights.get('domain_age', 0.10)
        domain_age = rule_results['source_analysis'].get('domain_age_days')
        if domain_age is not None:
            if domain_age > 730: # > 2 years
                adjustments += w_age
            elif domain_age < 90: # < 3 months
                adjustments -= w_age
            total_weight_used += w_age
            
        # 3. Fact Check (20%)
        w_fc = self.weights.get('fact_check', 0.20)
        fact_checks = rule_results.get('fact_checking', [])
        if fact_checks:
            fc_score = 0
            for fc in fact_checks:
                rating = fc.get('rating', '').lower()
                if rating in ['true', 'verified', 'correct']:
                    fc_score += 1
                elif rating in ['false', 'fake', 'incorrect']:
                    fc_score -= 1
            
            # Normalize fc_score (-1 to 1) roughly
            if fc_score > 0: adjustments += w_fc
            elif fc_score < 0: adjustments -= w_fc
            total_weight_used += w_fc
            
        # 4. Sentiment Neutrality (15%)
        # Extreme sentiment = lower score
        w_sent = self.weights.get('sentiment_neutrality', 0.15)
        sentiment = nlp_results.get('sentiment', {})
        if sentiment:
            s_score = sentiment.get('score', 0.5)
            # If extremely positive or negative (>0.9), penalize
            if s_score > 0.9:
                adjustments -= w_sent * 0.5 # Penalty for extremism
            else:
                adjustments += w_sent * 0.2 # Slight boost for moderation
            total_weight_used += w_sent
            
        # 5. Entity Presence (15%)
        # Presence of Named Entities (PER, ORG, LOC) suggests verifyiability
        w_ent = self.weights.get('entity_presence', 0.15)
        entities = nlp_results.get('named_entities', [])
        if len(entities) > 0:
            # More entities = better (capped)
            boost = min(1.0, len(entities) * 0.2) 
            adjustments += w_ent * boost
            total_weight_used += w_ent
            
        # 6. Text Coherence (15%) (Vocabulary Diversity)
        w_coh = self.weights.get('coherence', 0.15)
        coherence = nlp_results.get('coherence_score')
        if coherence is not None:
            # Coherence is usually 0.0 to 1.0
            # Center around 0.5: >0.5 improves, <0.5 penalizes
            adjustments += (coherence - 0.5) * w_coh
            total_weight_used += w_coh
            
        # Final calculation
        # Base 0.5 + sum of weighted adjustments
        # Adjustments are in range [-weight, +weight]
        
        final_score = 0.5 + adjustments
        
        return max(0.0, min(1.0, final_score))
    
    def generate_report(
        self,
        input_data: str,
        cleaned_text: str,
        rule_results: Dict,
        nlp_results: Dict,
        external_data: ExternalData,
        overall_score: float,
        web_content: Optional[WebContent] = None,
        graph_context: str = "" # [NEW]
    ) -> Dict[str, Any]:
        """Generate the final evaluation report."""
        
        report = {
            'idRapport': f"report_{int(datetime.datetime.now().timestamp())}",
            'informationEntree': input_data,
            'dateGeneration': datetime.datetime.now().isoformat(),
            'scoreCredibilite': round(overall_score, 2),
            'resumeAnalyse': "",
            'detailsScore': {
                'base': 0.5,
                'weights': self.weights,
                'factors': self._get_score_factors(rule_results, nlp_results)
            },
            'sourcesUtilisees': [],
            'reglesAppliquees': rule_results,
            'analyseNLP': {
                'sentiment': nlp_results.get('sentiment'),
                'bias_analysis': nlp_results.get('bias_analysis'),
                'named_entities_count': len(nlp_results.get('named_entities', [])),
                'coherence_score': nlp_results.get('coherence_score'),
                'sentiment_explanation_preview': (nlp_results.get('sentiment_explanation') or [])[:3]
            },
            'metadonnees': {}
        }
        
        # Add web content metadata if available
        if web_content:
            if web_content.success:
                report['metadonnees']['page_title'] = web_content.title
                report['metadonnees']['meta_description'] = web_content.meta_description
                report['metadonnees']['links_count'] = len(web_content.links)
            else:
                report['metadonnees']['warning'] = f"Content scrape failed: {web_content.error}"

        # Generate summary
        summary_parts = []
        
        if web_content and not web_content.success:
            summary_parts.append(f"⚠️ ATTENTION: Impossible de lire le texte de la page ({web_content.error}). Analyse basée uniquement sur la réputation du domaine.")
        
        if overall_score > 0.75:
            summary_parts.append("L'analyse suggère une crédibilité ÉLEVÉE.")
        elif overall_score > 0.55:
            summary_parts.append("L'analyse suggère une crédibilité MOYENNE à ÉLEVÉE.")
        elif overall_score > 0.45:
            summary_parts.append("L'analyse suggère une crédibilité MOYENNE.")
        elif overall_score > 0.25:
            summary_parts.append("L'analyse suggère une crédibilité FAIBLE à MOYENNE.")
        else:
            summary_parts.append("L'analyse suggère une crédibilité FAIBLE.")
        
        if external_data.source_reputation != 'Unknown':
            summary_parts.append(f"Réputation source : {external_data.source_reputation}.")
        
        if external_data.domain_age_days:
            years = external_data.domain_age_days / 365
            summary_parts.append(f"Âge du domaine : {years:.1f} ans.")
        
        if external_data.fact_checks:
            summary_parts.append(f"{len(external_data.fact_checks)} vérification(s) de faits trouvée(s).")
        
        report['resumeAnalyse'] = " ".join(summary_parts)
        
        # List sources used
        if self.is_url(input_data):
            report['sourcesUtilisees'].append({
                'type': 'Primary URL',
                'url': input_data
            })
        report['sourcesUtilisees'].append({
            'type': 'WHOIS Lookup',
            'status': 'Success' if (external_data.domain_info and external_data.domain_info.success) else 'Failed/N/A'
        })
        report['sourcesUtilisees'].append({
            'type': 'Fact Check API',
            'results_count': len(external_data.fact_checks)
        })
        
        return report
    
    def _get_score_factors(self, rule_results: Dict, nlp_results: Dict) -> List[Dict]:
        """Get list of factors that influenced the score (For UI)."""
        factors = []
        
        # 1. Reputation
        rep = rule_results['source_analysis'].get('reputation')
        if rep and "N/A" not in rep:
            factors.append({
                'factor': 'Source Reputation',
                'value': rep,
                'weight': f"{int(self.weights.get('source_reputation',0)*100)}%",
                'impact': '+' if rep == 'High' else ('-' if rep == 'Low' else '0')
            })
            
        # 2. Fact Checks
        if rule_results.get('fact_checking'):
             factors.append({
                'factor': 'Fact Checks',
                'value': f"{len(rule_results['fact_checking'])} found",
                'weight': f"{int(self.weights.get('fact_check',0)*100)}%",
                'impact': 'Variable'
            })

        # 3. Entities
        n_ent = len(nlp_results.get('named_entities', []))
        if n_ent > 0:
            factors.append({
                'factor': 'Entity Presence',
                'value': f"{n_ent} entities",
                'weight': f"{int(self.weights.get('entity_presence',0)*100)}%",
                'impact': '+'
            })
            
        # 4. Sentiment
        sent = nlp_results.get('sentiment', {})
        if sent:
            factors.append({
                'factor': 'Sentiment Neutrality',
                'value': f"{sent.get('label')} ({sent.get('score',0):.2f})",
                'weight': f"{int(self.weights.get('sentiment_neutrality',0)*100)}%",
                'impact': '-' if sent.get('score', 0) > 0.9 else '0'
            })

        return factors
    
    def verify_information(self, input_data: str) -> Dict[str, Any]:
        """
        Main pipeline to verify credibility of input data.
        
        Args:
            input_data: URL or text to verify
            
        Returns:
            Complete evaluation report
        """
        if not isinstance(input_data, str) or not input_data.strip():
            return {"error": "L'entrée doit être une chaîne non vide."}
        
        print(f"\n[SysCRED] === Vérification: {input_data[:100]}... ===")
        
        # 1. Determine input type and fetch content
        text_to_analyze = ""
        web_content = None
        is_url = self.is_url(input_data)
        
        if is_url:
            print("[SysCRED] Fetching web content...")
            web_content = self.api_clients.fetch_web_content(input_data)
            
            if web_content.success:
                text_to_analyze = web_content.text_content
                print(f"[SysCRED] ✓ Content fetched: {len(text_to_analyze)} chars")
            else:
                print(f"[SysCRED] ⚠ Fetch failed: {web_content.error}")
                print("[SysCRED] Proceeding with Domain/Metadata analysis only.")
                text_to_analyze = ""
                # We don't return error anymore, we proceed!
        else:
            text_to_analyze = input_data
        
        # 2. Preprocess text
        cleaned_text = self.preprocess(text_to_analyze)
        
        # Only error on empty text if it wasn't a failed web fetch
        # If web fetch failed, we proceed with empty text to give metadata analysis
        if not cleaned_text and not (is_url and web_content and not web_content.success):
            return {"error": "Le texte est vide après prétraitement."}
        print(f"[SysCRED] Preprocessed text: {len(cleaned_text)} chars")
        
        # Determine best query for Fact Checking
        fact_check_query = input_data
        if text_to_analyze and len(text_to_analyze) > 10:
             # Use start of text if available
            fact_check_query = text_to_analyze[:200]
        elif is_url and web_content and web_content.title:
            # Fallback to page title if text is missing (e.g. 403)
            fact_check_query = web_content.title
        
        # 3. Fetch external data
        print(f"[SysCRED] Fetching external data (Query: {fact_check_query[:50]}...)...")
        external_data = self.api_clients.fetch_external_data(input_data, fc_query=fact_check_query)
        
        # [FIX] Handle text-only input reputation
        if not is_url:
            external_data.source_reputation = "N/A (User Input)"
            
        print(f"[SysCRED] ✓ Reputation: {external_data.source_reputation}, Age: {external_data.domain_age_days} days")
        
        # 4. Rule-based analysis
        print("[SysCRED] Running rule-based analysis...")
        rule_results = self.rule_based_analysis(cleaned_text, external_data)
        
        # 5. NLP analysis
        print("[SysCRED] Running NLP analysis...")
        nlp_results = self.nlp_analysis(cleaned_text)
        
        # 6. Calculate score
        overall_score = self.calculate_overall_score(rule_results, nlp_results)
        print(f"[SysCRED] ✓ Credibility score: {overall_score:.2f}")

        # 7. [NEW] GraphRAG Context Retrieval
        graph_context = ""
        similar_uris = []
        if self.graph_rag and 'source_analysis' in rule_results:
             domain = rule_results['source_analysis'].get('domain', '')
             # Pass keywords for text search if domain is empty or generic
             keywords = []
             if not domain and cleaned_text:
                 keywords = cleaned_text.split()[:5] # Simple keyword extraction
                 
             context = self.graph_rag.get_context(domain, keywords=keywords)
             graph_context = context.get('full_text', '')
             similar_uris = context.get('similar_uris', [])
             
             if "Graph Memory" in graph_context:
                 print(f"[SysCRED] GraphRAG Context Found: {graph_context.splitlines()[1]}")

        # 8. Generate report (Updated to include context)
        report = self.generate_report(
            input_data, cleaned_text, rule_results, 
            nlp_results, external_data, overall_score, web_content,
            graph_context=graph_context
        )
        
        # Add similar URIs to report for ontology linking
        if similar_uris:
            report['similar_claims_uris'] = similar_uris

        # 9. Save to ontology
        if self.ontology_manager:
            try:
                report_uri = self.ontology_manager.add_evaluation_triplets(report)
                report['ontology_uri'] = report_uri
                self.ontology_manager.save_data()
            except Exception as e:
                print(f"[SysCRED] Ontology save failed: {e}")
        
        print("[SysCRED] === Vérification terminée ===\n")
        return report


# --- Main / Testing ---
if __name__ == "__main__":
    import json
    
    print("=" * 60)
    print("SysCRED v2.0 - Système de Vérification de Crédibilité")
    print("(c) Dominique S. Loyer - PhD Thesis Prototype")
    print("=" * 60 + "\n")
    
    # Initialize system (without ML models for quick testing)
    system = CredibilityVerificationSystem(
        ontology_base_path="/Users/bk280625/documents041025/MonCode/sysCRED_onto26avrtil.ttl",
        ontology_data_path="/Users/bk280625/documents041025/MonCode/ontology/sysCRED_data.ttl",
        load_ml_models=False  # Set to True for full analysis
    )
    
    # Test cases
    test_cases = {
        "Test URL Crédible": "https://www.lemonde.fr",
        "Test URL Inconnu": "https://example.com/article",
        "Test Texte Simple": "This is a verified and authentic news report.",
        "Test Texte Suspect": "Shocking conspiracy revealed! They don't want you to know this secret!",
    }
    
    results = {}
    for name, test_input in test_cases.items():
        print(f"\n{'='*50}")
        print(f"Test: {name}")
        print('='*50)
        
        result = system.verify_information(test_input)
        results[name] = result
        
        if 'error' not in result:
            print(f"\nScore: {result['scoreCredibilite']}")
            print(f"Résumé: {result['resumeAnalyse']}")
        else:
            print(f"Erreur: {result['error']}")
    
    print("\n" + "="*60)
    print("Résumé des tests:")
    print("="*60)
    for name, result in results.items():
        if 'error' not in result:
            print(f"  {name}: Score = {result['scoreCredibilite']:.2f}")
        else:
            print(f"  {name}: ERREUR")
