import re
import requests # Gardé pour d'éventuels appels API réels
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
import torch # Nécessaire pour certains modèles transformers
# LIME est conservé pour l'explicabilité, mais d'autres techniques pourraient être nécessaires
# pour différents types de modèles (ex: SHAP).
from lime.lime_text import LimeTextExplainer
from urllib.parse import urlparse # Pour analyser les URLs
import datetime # Pour la date de génération du rapport
# --- (c)Dominique S. Loyer ---
# code in Python by Dominique S. Loyer
# May 2025
# please use this citation key if you use it
# Citation Key: loyerModelingHybridSystem2025
#
#
#        Certains modèles peuvent nécessiter un fine-tuning.
# --- Configuration Initiale (Modèles et Explainers) ---
# On charge les modèles ici pour éviter de les recharger à chaque appel.
# NOTE : Pour une application réelle, envisagez des modèles plus spécifiques
#        pour la détection de biais, la cohérence, etc.
#        Certains modèles peuvent nécessiter un fine-tuning.

# Modèle de sentiment 
sentiment_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Modèle pour la détection de biais 
# Remplacer par un modèle entraîné pour la détection de biais.
# Exemple : 'd4data/bias-detection-model' (vérifier disponibilité sur Hugging Face Hub)
# Pour l'instant, on utilise un modèle de classification générique comme placeholder.
bias_tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
bias_model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased") # PLACEHOLDER

# Modèle pour la Reconnaissance d'Entités Nommées (NER)
ner_pipeline = pipeline("ner", grouped_entities=True) # grouped_entities est souvent utile

# Explainer LIME 
# Note : L'explicabilité pour d'autres modèles (ex: biais) nécessiterait une configuration adaptée.
explainer = LimeTextExplainer(class_names=['NEGATIVE', 'POSITIVE']) # Ajuster si le modèle a d'autres classes

# --- Fonctions Utilitaires ---

def is_url(text):
    """Vérifie si une chaîne ressemble à une URL."""
    try:
        result = urlparse(text)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def fetch_web_content(url):
    """
    Simule la récupération du contenu textuel d'une URL.
    Pour une implémentation réelle, utiliser `requests` et `BeautifulSoup`.
    """
    print(f"[Simulation] Récupération du contenu de : {url}")
    # Simuler différents contenus pour tester
    if "verified-news.com" in url:
        return "This official report is verified and credible. All facts checked."
    elif "hoax-site.org" in url:
        return "Shocking conspiracy revealed! Experts are wrong. This is a hoax!"
    else:
        # Simuler le cas où une URL ne retourne rien ou est inaccessible
        if "nonexistent-domain-for-test.xyz" in url:
             print(f"[Simulation] Échec de la récupération pour : {url}")
             return None # Simule un échec
        return "Some generic content from the web."

def fetch_external_data(text_or_url):
    """
    Simule la récupération de données externes (fact-checking, réputation source).
    Pour une implémentation réelle, appeler des API (Google Fact Check, NewsGuard, etc.).
    """
    print(f"[Simulation] Recherche de données externes pour : {str(text_or_url)[:50]}...") # Assurer que c'est une str pour le slicing
    external_info = {
        'fact_checks': [],
        'source_reputation': 'Unknown',
        'domain_age_days': None, # Initialisé à None
        'related_articles': []
    }
    # Tente de récupérer les infos uniquement si c'est une URL valide
    if isinstance(text_or_url, str) and is_url(text_or_url):
        domain = urlparse(text_or_url).netloc
        if "verified-news.com" in domain:
            external_info['source_reputation'] = 'High'
            external_info['domain_age_days'] = 1500 # Défini seulement pour les URLs reconnues
            external_info['fact_checks'].append({'claim': 'Official report facts', 'rating': 'True'})
        elif "hoax-site.org" in domain:
            external_info['source_reputation'] = 'Low'
            external_info['domain_age_days'] = 90 # Défini seulement pour les URLs reconnues
            external_info['fact_checks'].append({'claim': 'Conspiracy theory', 'rating': 'False'})
        elif "nonexistent-domain-for-test.xyz" not in domain: # Ne pas donner d'âge pour le domaine inexistant
             external_info['source_reputation'] = 'Medium'
             external_info['domain_age_days'] = 730 # Défini seulement pour les URLs reconnues

    # Simulation de résultats de recherche (peut être ajouté même si ce n'est pas une URL)
    external_info['related_articles'] = [
        {'title': 'Related Story A', 'url': 'http://example.com/a'},
        {'title': 'Related Story B', 'url': 'http://example.com/b'}
    ]
    return external_info

# --- Classe Principale du Système ---

class CredibilityVerificationSystem:
    def __init__(self):
        # Les modèles sont chargés globalement, on peut les référencer ici si besoin
        self.sentiment_pipeline = sentiment_pipeline
        self.ner_pipeline = ner_pipeline
        self.bias_tokenizer = bias_tokenizer
        self.bias_model = bias_model
        self.explainer = explainer

    def preprocess(self, text):
        """Nettoyage simple du texte."""
        # Améliorable : suppression de HTML, normalisation unicode, etc.
        if not isinstance(text, str): # Vérifier si l'entrée est bien une chaîne
             return ""
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE) # Enlever les URLs
        text = re.sub(r'\s+', ' ', text) # Normaliser les espaces
        text = re.sub(r'[^\w\s\.\?,!]', '', text) # Garder ponctuation basique
        return text.lower().strip()

    def rule_based_analysis(self, text, external_data):
        """
        Analyse basée sur des règles logiques prédéfinies et des données externes.
        Ceci est une version simplifiée basée sur le PDF.
        """
        results = {
            'linguistic_markers': {},
            'source_analysis': {},
            'timeliness_flags': []
        }
        # 1. Marqueurs Linguistiques (Exemples simples)
        sensational_words = ['shocking', 'revealed', 'conspiracy', 'amazing', 'secret']
        certainty_words = ['verified', 'authentic', 'credible', 'proven', 'fact']
        doubt_words = ['hoax', 'false', 'fake', 'unproven', 'rumor']

        results['linguistic_markers']['sensationalism'] = sum(1 for word in sensational_words if word in text)
        results['linguistic_markers']['certainty'] = sum(1 for word in certainty_words if word in text)
        results['linguistic_markers']['doubt'] = sum(1 for word in doubt_words if word in text)

        # 2. Analyse de la Source (basée sur les données externes simulées)
        results['source_analysis']['reputation'] = external_data.get('source_reputation', 'Unknown')
        domain_age = external_data.get('domain_age_days') # Récupérer la valeur (peut être None)
        results['source_analysis']['domain_age_days'] = domain_age # Stocker la valeur récupérée

        # 3. Actualité 
        # *** CORRECTION ICI ***
        # Vérifier si domain_age n'est PAS None AVANT de comparer
        if domain_age is not None and domain_age < 180: # Moins de 6 mois
             results['timeliness_flags'].append('Source domain is relatively new.')

        # 4. Vérification des Faits (Fact-Checking)
        results['fact_checking'] = external_data.get('fact_checks', [])

        return results

    def nlp_analysis(self, text):
        """
        Analyse via des modèles NLP (IA).
        """
        results = {
            'sentiment': None,
            'sentiment_explanation': None,
            'bias_analysis': {'score': None, 'label': 'Unavailable'}, # Placeholder
            'named_entities': None,
            'coherence_score': None # Placeholder
        }

        # Vérification supplémentaire si le texte est vide après preprocess
        if not text:
             print("Avertissement : Texte vide fourni à nlp_analysis.")
             results['sentiment'] = {'label': 'Neutral', 'score': 0.5} # Ou une autre valeur par défaut
             return results # Retourner les résultats par défaut

        # 1. Analyse de Sentiment (avec explicabilité LIME)
        try:
            # Prédiction pour LIME
            def predict_proba_sentiment(texts):
                # S'assurer que texts est une liste de chaînes
                if isinstance(texts, str):
                    texts = [texts]
                elif not isinstance(texts, list):
                    texts = list(texts) # Tenter de convertir en liste

                processed_texts = [self.preprocess(t) for t in texts]
                # Gérer les textes vides après prétraitement
                valid_texts = [t for t in processed_texts if t]
                probabilities = []

                if not valid_texts:
                    # Retourner une distribution neutre pour chaque texte original si tous sont vides
                    return np.array([[0.5, 0.5]] * len(texts))

                # Faire la prédiction uniquement sur les textes valides
                predictions = self.sentiment_pipeline(valid_texts)
                pred_idx = 0
                for original_text in processed_texts:
                    if original_text: # Si le texte original n'était pas vide après preprocess
                        pred = predictions[pred_idx]
                        # Assurer que la sortie est toujours [prob_neg, prob_pos]
                        if pred['label'] == 'POSITIVE':
                            probabilities.append([1 - pred['score'], pred['score']])
                        else: # NEGATIVE or other label mapped to negative
                            probabilities.append([pred['score'], 1 - pred['score']])
                        pred_idx += 1
                    else:
                         probabilities.append([0.5, 0.5]) # Probabilité neutre pour texte vide

                return np.array(probabilities)

            # Obtenir la prédiction principale pour le texte unique
            main_prediction = self.sentiment_pipeline(text)[0]
            results['sentiment'] = main_prediction

            # Générer l'explication LIME
            explanation = self.explainer.explain_instance(
                text,
                predict_proba_sentiment,
                num_features=6 # Nombre de mots/features à montrer dans l'explication
            )
            results['sentiment_explanation'] = explanation.as_list()

        except Exception as e:
            print(f"Erreur lors de l'analyse de sentiment ou LIME : {e}")
            results['sentiment'] = {'label': 'Error', 'score': 0.0}
            results['sentiment_explanation'] = []

        # 2. Analyse de Biais (Simulation/Placeholder)
        # Un vrai modèle de détection de biais serait nécessaire ici.
        try:
            inputs = self.bias_tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
            with torch.no_grad():
                logits = self.bias_model(**inputs).logits
            simulated_bias_score = torch.softmax(logits, dim=1)[0][0].item() # Exemple
            if simulated_bias_score > 0.7: # Seuil arbitraire
                 results['bias_analysis'] = {'score': simulated_bias_score, 'label': 'Potential Bias Flagged (Simulated)'}
            else:
                 results['bias_analysis'] = {'score': simulated_bias_score, 'label': 'Low Bias Detected (Simulated)'}
        except Exception as e:
            print(f"Erreur lors de l'analyse de biais (simulée) : {e}")
            results['bias_analysis'] = {'score': None, 'label': 'Error'}


        # 3. Reconnaissance d'Entités Nommées (NER)
        try:
            entities = self.ner_pipeline(text)
            results['named_entities'] = entities
        except Exception as e:
            print(f"Erreur lors de l'analyse NER : {e}")
            results['named_entities'] = []

        # 4. Analyse de Cohérence (Placeholder)
        results['coherence_score'] = np.random.rand() # Score aléatoire pour l'exemple

        return results

    def calculate_overall_score(self, rule_results, nlp_results):
        """
        Calcule un score de crédibilité global basé sur les analyses.
        Ceci est une heuristique simple, à affiner considérablement.
        Le score va de 0 (peu crédible) à 1 (très crédible).
        """
        score = 0.5 # Score de base neutre
        weight_sum = 1.0 # Pour normaliser les poids ajoutés/soustraits
        score_adjustment = 0.0

        # --- Pondérations (Exemples - À AJUSTER ABSOLUMENT) ---
        WEIGHT_REPUTATION = 0.3
        WEIGHT_AGE = 0.05
        WEIGHT_CERTAINTY = 0.1
        WEIGHT_DOUBT = 0.15
        WEIGHT_SENSATIONALISM = 0.1
        WEIGHT_NEGATIVE_SENTIMENT = 0.05
        WEIGHT_BIAS = 0.15
        WEIGHT_COHERENCE = 0.05 # Faible car simulé

        # Facteurs basés sur les règles
        if rule_results['source_analysis']['reputation'] == 'High':
            score_adjustment += WEIGHT_REPUTATION
            weight_sum += WEIGHT_REPUTATION
        elif rule_results['source_analysis']['reputation'] == 'Low':
            score_adjustment -= WEIGHT_REPUTATION
            weight_sum += WEIGHT_REPUTATION

        domain_age = rule_results['source_analysis'].get('domain_age_days')
        # *** CORRECTION ICI AUSSI *** Vérifier si domain_age n'est pas None
        if domain_age is not None:
            if domain_age > 365 * 2: # Ex: > 2 ans
                 score_adjustment += WEIGHT_AGE
                 weight_sum += WEIGHT_AGE
            elif domain_age < 90: # Ex: < 3 mois
                 score_adjustment -= WEIGHT_AGE
                 weight_sum += WEIGHT_AGE


        if rule_results['linguistic_markers']['certainty'] > 0 and rule_results['linguistic_markers']['doubt'] == 0:
             score_adjustment += WEIGHT_CERTAINTY * rule_results['linguistic_markers']['certainty'] # Plus de certitude = plus de poids
             weight_sum += WEIGHT_CERTAINTY * rule_results['linguistic_markers']['certainty']
        elif rule_results['linguistic_markers']['doubt'] > 0:
             score_adjustment -= WEIGHT_DOUBT * rule_results['linguistic_markers']['doubt'] # Pénaliser plus si plusieurs mots
             weight_sum += WEIGHT_DOUBT * rule_results['linguistic_markers']['doubt']

        if rule_results['linguistic_markers']['sensationalism'] > 0:
            sensationalism_penalty = min(WEIGHT_SENSATIONALISM * rule_results['linguistic_markers']['sensationalism'], WEIGHT_SENSATIONALISM * 3)
            score_adjustment -= sensationalism_penalty
            weight_sum += sensationalism_penalty

        # Facteurs basés sur le NLP
        if nlp_results.get('sentiment'): # Vérifier que la clé 'sentiment' existe
            if nlp_results['sentiment']['label'] == 'NEGATIVE' and nlp_results['sentiment']['score'] > 0.85:
                 score_adjustment -= WEIGHT_NEGATIVE_SENTIMENT
                 weight_sum += WEIGHT_NEGATIVE_SENTIMENT

        if nlp_results.get('bias_analysis') and 'Flagged' in nlp_results['bias_analysis'].get('label',''):
             bias_score_value = nlp_results['bias_analysis'].get('score')
             if bias_score_value is not None:
                 bias_impact = WEIGHT_BIAS * ((bias_score_value - 0.5) * 2) # Normaliser le score de biais (0.5->0, 1.0->1)
                 score_adjustment -= bias_impact # Soustraire l'impact du biais
                 weight_sum += WEIGHT_BIAS # Ajouter le poids du facteur biais

        if nlp_results.get('coherence_score') is not None:
             coherence_adjustment = (nlp_results['coherence_score'] - 0.5) * WEIGHT_COHERENCE
             score_adjustment += coherence_adjustment
             weight_sum += abs(coherence_adjustment)

        # Calcul final
        final_score = 0.5 + score_adjustment / weight_sum if weight_sum > 0 else 0.5

        return max(0.0, min(1.0, final_score)) # Assurer que le score reste entre 0 et 1


    def generate_report(self, input_data, cleaned_text, rule_results, nlp_results, external_data, overall_score):
        """
        Génère le rapport final structuré, similaire à 'RapportEvaluation' du PDF.
        """
        report = {
            'idRapport': f"report_{int(datetime.datetime.now().timestamp())}",
            'informationEntree': input_data,
            'dateGeneration': datetime.datetime.now().isoformat(),
            'scoreCredibilite': round(overall_score, 2),
            'resumeAnalyse': "", # Sera généré ci-dessous
            'detailsScore': {
                'base': 0.5,
                'adjustments': self._get_score_adjustments(rule_results, nlp_results)
            },
            'sourcesUtilisees': [], # Lister les sources externes consultées
            'reglesAppliquees': rule_results,
            'analyseNLP': { # Filtrer pour ne pas inclure les explications potentiellement longues ici
                 'sentiment': nlp_results.get('sentiment'),
                 'bias_analysis': nlp_results.get('bias_analysis'),
                 'named_entities_count': len(nlp_results.get('named_entities', [])),
                 'coherence_score': nlp_results.get('coherence_score'),
                 'sentiment_explanation_preview': nlp_results.get('sentiment_explanation', [])[:2] # Juste un aperçu
            },
        }

        # Générer un résumé textuel simple
        summary_parts = []
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


        if rule_results['source_analysis']['reputation'] != 'Unknown':
             summary_parts.append(f"Réputation source : {rule_results['source_analysis']['reputation']}.")
        elif isinstance(input_data, str) and is_url(input_data): # Seulement si c'était une URL mais réputation inconnue
             summary_parts.append("Réputation source : Inconnue.")


        if rule_results['linguistic_markers']['sensationalism'] > 0:
             summary_parts.append(f"Marqueurs sensationnalistes détectés ({rule_results['linguistic_markers']['sensationalism']}).")
        if rule_results['linguistic_markers']['doubt'] > 0:
             summary_parts.append(f"Marqueurs de doute détectés ({rule_results['linguistic_markers']['doubt']}).")

        bias_info = nlp_results.get('bias_analysis')
        if bias_info and 'Flagged' in bias_info.get('label',''):
             bias_score_str = f"{bias_info.get('score', 'N/A'):.2f}" if isinstance(bias_info.get('score'), float) else 'N/A'
             summary_parts.append(f"Biais potentiel signalé (Score simulé: {bias_score_str}).")

        if rule_results['fact_checking']:
             fc_summary = ", ".join([f"{fc['claim']} ({fc['rating']})" for fc in rule_results['fact_checking']])
             summary_parts.append(f"Vérifications externes trouvées : {fc_summary}.")
        elif isinstance(input_data, str) and is_url(input_data): # Si c'était une URL mais pas de fact check trouvé
             summary_parts.append("Aucune vérification externe spécifique trouvée (simulation).")


        report['resumeAnalyse'] = " ".join(summary_parts)

        # Lister les sources externes (exemple)
        is_input_url_flag = isinstance(input_data, str) and is_url(input_data)
        if is_input_url_flag:
             report['sourcesUtilisees'].append({'type': 'Primary Input URL', 'url': input_data})
        report['sourcesUtilisees'].append({'type': 'External Reputation Check', 'details': f"Reputation: {rule_results['source_analysis']['reputation']} (Simulated)"})
        report['sourcesUtilisees'].append({'type': 'External Fact Check API', 'details': f"{len(rule_results['fact_checking'])} checks found (Simulated)"})


        return report

    def _get_score_adjustments(self, rule_results, nlp_results):
        """Helper pour lister les ajustements de score pour le rapport."""
        adjustments = []
        # Miroir de la logique dans calculate_overall_score, mais juste pour le reporting
        if rule_results['source_analysis']['reputation'] == 'High':
            adjustments.append({'factor': 'Source Reputation', 'value': '+High'})
        elif rule_results['source_analysis']['reputation'] == 'Low':
            adjustments.append({'factor': 'Source Reputation', 'value': '-Low'})

        domain_age = rule_results['source_analysis'].get('domain_age_days')
        if domain_age is not None:
            if domain_age > 365 * 2:
                 adjustments.append({'factor': 'Domain Age', 'value': '+Old'})
            elif domain_age < 90:
                 adjustments.append({'factor': 'Domain Age', 'value': '-New'})

        certainty = rule_results['linguistic_markers']['certainty']
        doubt = rule_results['linguistic_markers']['doubt']
        if certainty > 0 and doubt == 0:
             adjustments.append({'factor': 'Certainty Markers', 'value': f"+{certainty}"})
        elif doubt > 0:
             adjustments.append({'factor': 'Doubt Markers', 'value': f"-{doubt}"})

        sensationalism = rule_results['linguistic_markers']['sensationalism']
        if sensationalism > 0:
            adjustments.append({'factor': 'Sensationalism', 'value': f"-{sensationalism}"})

        sentiment_info = nlp_results.get('sentiment')
        if sentiment_info:
            if sentiment_info['label'] == 'NEGATIVE' and sentiment_info['score'] > 0.85:
                 adjustments.append({'factor': 'Strong Negative Sentiment', 'value': '-Impact'})

        bias_info = nlp_results.get('bias_analysis')
        if bias_info and 'Flagged' in bias_info.get('label',''):
             bias_score_str = f"{bias_info.get('score', 0):.2f}" if isinstance(bias_info.get('score'), float) else 'N/A'
             adjustments.append({'factor': 'Potential Bias', 'value': f"-Impact (Score: {bias_score_str})"})

        coherence_score = nlp_results.get('coherence_score')
        if coherence_score is not None:
             adj_val = round((coherence_score - 0.5), 2)
             adjustments.append({'factor': 'Coherence (Simulated)', 'value': f"{'+' if adj_val >= 0 else ''}{adj_val}"})

        return adjustments


    def verify_information(self, input_data):
        """
        Pipeline principal pour vérifier la crédibilité (adapté du PDF).
        """
         # Vérification initiale du type d'entrée
        if not isinstance(input_data, str) or not input_data.strip():
            print("Erreur: L'entrée fournie n'est pas une chaîne de caractères valide ou est vide.")
            return {"error": "L'entrée doit être une chaîne de caractères non vide (texte ou URL)."}

        print(f"\n--- Vérification pour : {input_data[:100]}... ---")

        # 1. Déterminer le type d'entrée et récupérer le contenu si URL
        text_to_analyze = ""
        is_input_url = is_url(input_data)
        if is_input_url:
            try:
                # --- Simulation ---
                text_to_analyze = fetch_web_content(input_data)
                if text_to_analyze is None: # Gérer l'échec simulé de fetch_web_content
                     print(f"Échec de la récupération du contenu pour l'URL : {input_data}")
                     return {"error": f"Impossible de récupérer le contenu de l'URL : {input_data}"}

            except requests.exceptions.RequestException as e: # Garder pour une future implémentation réelle
                 print(f"Erreur réseau/HTTP lors de la récupération de l'URL {input_data}: {e}")
                 return {"error": f"Erreur réseau lors de la récupération de l'URL : {e}"}
            except Exception as e:
                 print(f"Erreur inattendue lors du traitement de l'URL {input_data}: {e}")
                 return {"error": f"Erreur inattendue lors du traitement de l'URL : {e}"}

        else: # Si ce n'est pas une URL, c'est du texte direct
            text_to_analyze = input_data

        # 2. Prétraitement du texte
        cleaned_text = self.preprocess(text_to_analyze)
        if not cleaned_text:
             # Gérer le cas où le texte est vide après nettoyage
             print("Erreur: Le texte est vide après prétraitement.")
             return {"error": "Le texte fourni est vide ou ne contient que des éléments supprimés lors du prétraitement."}
        print(f"Texte nettoyé (extrait) : {cleaned_text[:200]}...")

        # 3. Récupérer les données externes
        external_data = fetch_external_data(input_data if is_input_url else cleaned_text)
        print(f"Données externes (simulées) : {external_data}")

        # 4. Analyse basée sur les règles
        rule_results = self.rule_based_analysis(cleaned_text, external_data)
        print(f"Résultats règles : {rule_results}")

        # 5. Analyse basée sur NLP/IA
        nlp_results = self.nlp_analysis(cleaned_text)
        print(f"Résultats NLP (Sentiment): {nlp_results.get('sentiment')}")
        print(f"Résultats NLP (Bias): {nlp_results.get('bias_analysis')}")
        print(f"Résultats NLP (NER count): {len(nlp_results.get('named_entities', []))}")

        # 6. Calculer le score global
        overall_score = self.calculate_overall_score(rule_results, nlp_results)
        print(f"Score global calculé : {overall_score:.2f}")

        # 7. Générer le rapport final
        final_report = self.generate_report(input_data, cleaned_text, rule_results, nlp_results, external_data, overall_score)

        return final_report

# --- Tests du Système ---
if __name__ == "__main__":
    system = CredibilityVerificationSystem()
    results = {} # Dictionnaire pour stocker les résultats

    test_cases = {
        "Test 1 (Texte Simple)": "This post is verified and credible. Avoid false information.",
        "Test 2 (URL Crédible)": "http://verified-news.com/article123",
        "Test 3 (URL Hoax)": "http://hoax-site.org/the-truth",
        "Test 4 (Texte Sensationnaliste)": "Shocking news! The secret is revealed! This changes everything! Amazing discovery!",
        "Test 5 (Texte Vide)": " ",
        "Test 6 (URL Inexistante)": "http://nonexistent-domain-for-test.xyz",
        "Test 7 (URL Générique)": "http://example-generic-site.com/page",
        "Test 8 (Texte avec Doute)": "There are rumors and claims that this might be a hoax.",
    }

    import json

    for test_name, test_input in test_cases.items():
        print(f"\n===== Exécution: {test_name} =====")
        result = system.verify_information(test_input)
        results[test_name] = result # Stocker le résultat
        print(f"\n--- Rapport Final {test_name} ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(f"===== Fin: {test_name} =====")

    # Optionnel: Afficher un résumé de tous les scores à la fin
    print("\n\n===== Résumé des Scores =====")
    for test_name, result in results.items():
         score = result.get('scoreCredibilite', 'Erreur')
         if score == 'Erreur' and 'error' in result:
              score = f"Erreur ({result['error']})"
         print(f"{test_name}: {score}")

