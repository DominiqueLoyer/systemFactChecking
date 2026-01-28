import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ajout du chemin pour importer les modules de SysCRED
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importation des modules à tester (ajustez les chemins selon votre structure)
# Nous supposons une structure où ce fichier est à la racine ou dans un dossier 'tests'
try:
    from syscred.verification_system import VerificationSystem, ContentAnalyzer, SourceVerifier
    from syscred.ontology_manager import OntologyManager
    from syscred.seo_analyzer import SEOScorer
except ImportError:
    # Fallback pour une exécution depuis le dossier 'syscred' lui-même
    from verification_system import VerificationSystem, ContentAnalyzer, SourceVerifier
    from ontology_manager import OntologyManager
    from seo_analyzer import SEOScorer


class TestVerificationSystemNLP(unittest.TestCase):
    """
    Tests unitaires pour le module d'analyse de contenu (NLP) - 'Système 1'.
    Vérifie le chargement des modèles et la cohérence des scores sur des textes simples.
    """
    
    @classmethod
    def setUpClass(cls):
        """Charge les modèles NLP une seule fois pour tous les tests."""
        print("\n[Init] Chargement des modèles NLP pour les tests... (peut prendre quelques secondes)")
        cls.analyzer = ContentAnalyzer()

    def test_coherence_score_coherent_text(self):
        """Test: Un texte cohérent doit avoir un score de cohérence élevé."""
        text = "L'intelligence artificielle est un domaine en pleine expansion. Les modèles de langage deviennent de plus en plus performants. Cela ouvre de nouvelles perspectives pour la recherche."
        score = self.analyzer.get_coherence_score(text)
        print(f"   -> Score cohérence (texte cohérent): {score:.2f}")
        self.assertGreater(score, 0.7, "Le score de cohérence devrait être élevé (>0.7) pour un texte structuré.")

    def test_coherence_score_incoherent_text(self):
        """Test: Un texte incohérent doit avoir un score de cohérence faible."""
        text = "Le chat mange une pomme. Il fait beau demain. La racine carrée de pi est complexe. J'aime les voitures rouges."
        score = self.analyzer.get_coherence_score(text)
        print(f"   -> Score cohérence (texte incohérent): {score:.2f}")
        self.assertLess(score, 0.6, "Le score de cohérence devrait être faible (<0.6) pour un texte décousu.")
        
    def test_bias_detection_neutral(self):
        """Test: Un texte factuel doit être détecté comme peu biaisé."""
        text = "La réunion a débuté à 10h00 et s'est terminée à 11h30. Les participants ont discuté du budget annuel."
        score, label = self.analyzer.get_bias_score(text)
        print(f"   -> Biais (neutre): Score={score:.2f}, Label={label}")
        # Note: Le comportement exact dépend du modèle, on suppose ici qu'un score bas = peu de biais détecté
        self.assertLess(score, 0.5, "Le score de biais devrait être faible pour un texte factuel.")
        self.assertIn(label.lower(), ['non-biased', 'neutral'], "Le label devrait indiquer une absence de biais.")

    def test_bias_detection_biased(self):
        """Test: Un texte avec un langage chargé doit être détecté comme biaisé."""
        text = "C'est une décision absolument scandaleuse et catastrophique qui va ruiner notre pays ! Il est évident qu'ils sont incompétents."
        score, label = self.analyzer.get_bias_score(text)
        print(f"   -> Biais (chargé): Score={score:.2f}, Label={label}")
        self.assertGreater(score, 0.6, "Le score de biais devrait être élevé pour un langage émotionnel/partisan.")
        self.assertIn(label.lower(), ['biased'], "Le label devrait indiquer la présence d'un biais.")


class TestVerificationSystemSymbolic(unittest.TestCase):
    """
    Tests unitaires pour le module de vérification des sources - 'Système 2'.
    Utilise des 'mocks' pour simuler les APIs externes (Google, WHOIS, etc.)
    afin de tester la logique sans dépendance réseau.
    """

    def setUp(self):
        self.verifier = SourceVerifier()

    @patch('syscred.api_clients.GoogleFactCheckClient.check_claim')
    def test_fact_check_proven_false(self, mock_check_claim):
        """Test: Une affirmation fausse connue doit retourner un score de 0.0."""
        # Configuration du mock : On simule une réponse de l'API disant que c'est faux
        mock_check_claim.return_value = {
            "found": True,
            "rating": "False",
            "source": "Snopes",
            "url": "http://snopes.com/factcheck/exemple"
        }
        
        claim = "La Terre est plate."
        result = self.verifier.verify_claim_factuality(claim)
        
        print(f"   -> Fact-check (Faux connu): Score={result['score']}, Source={result['evidence'].get('source')}")
        self.assertEqual(result['score'], 0.0, "Le score doit être 0.0 pour une affirmation prouvée fausse.")
        self.assertTrue(result['evidence']['found'])

    @patch('syscred.api_clients.GoogleFactCheckClient.check_claim')
    def test_fact_check_proven_true(self, mock_check_claim):
        """Test: Une affirmation vraie connue doit retourner un score de 1.0."""
        # Configuration du mock : On simule une réponse de l'API disant que c'est vrai
        mock_check_claim.return_value = {
            "found": True,
            "rating": "True",
            "source": "AFP Factuel",
            "url": "http://factuel.afp.com/exemple"
        }
        
        claim = "Paris est la capitale de la France."
        result = self.verifier.verify_claim_factuality(claim)
        
        print(f"   -> Fact-check (Vrai connu): Score={result['score']}, Source={result['evidence'].get('source')}")
        self.assertEqual(result['score'], 1.0, "Le score doit être 1.0 pour une affirmation prouvée vraie.")

    @patch('syscred.api_clients.GoogleFactCheckClient.check_claim')
    def test_fact_check_unknown(self, mock_check_claim):
        """Test: Une affirmation sans fact-check doit retourner un score neutre (0.5)."""
        # Configuration du mock : On simule qu'aucun fact-check n'a été trouvé
        mock_check_claim.return_value = {"found": False}
        
        claim = "Une affirmation obscure et très spécifique qui n'a pas été vérifiée."
        result = self.verifier.verify_claim_factuality(claim)
        
        print(f"   -> Fact-check (Inconnu): Score={result['score']}")
        self.assertEqual(result['score'], 0.5, "Le score doit être neutre (0.5) si aucun fact-check n'existe.")

    @patch('syscred.seo_analyzer.SEOScorer.get_domain_age')
    @patch('syscred.seo_analyzer.SEOScorer.get_estimated_backlinks')
    def test_source_reputation_heuristic(self, mock_backlinks, mock_domain_age):
        """Test: L'heuristique de réputation combine l'âge et les backlinks (simulés)."""
        # Simulation d'un site établi (vieux + beaucoup de liens)
        mock_domain_age.return_value = 15 * 365  # 15 ans
        mock_backlinks.return_value = 50000      # Beaucoup de liens

        domain = "lemonde.fr"
        score, details = self.verifier.assess_source_reputation(domain)
        
        print(f"   -> Réputation (Site établi): Score={score:.2f}, Âge={details['age_years']:.1f} ans, Backlinks={details['backlinks_est']}")
        self.assertGreater(score, 0.7, "Un vieux domaine avec beaucoup de backlinks devrait avoir un bon score de réputation.")

        # Simulation d' un site récent (jeune + peu de liens)
        mock_domain_age.return_value = 0.1 * 365 # 1 mois
        mock_backlinks.return_value = 50         # Peu de liens
        
        domain = "nouveau-site-douteux.xyz"
        score_new, details_new = self.verifier.assess_source_reputation(domain)
        print(f"   -> Réputation (Site récent): Score={score_new:.2f}")
        self.assertLess(score_new, 0.4, "Un domaine très récent avec peu de liens devrait avoir un faible score de réputation.")


class TestIntegrationFullPipeline(unittest.TestCase):
    """
    Test d'intégration du pipeline complet SysCRED.
    Utilise des mocks pour les parties externes, mais teste l'assemblage final.
    """
    
    @classmethod
    def setUpClass(cls):
        # On charge le système complet. Les sous-composants seront mockés dans le test.
        # Cela permet de tester la logique d'orchestration de VerificationSystem.
        cls.system = VerificationSystem()
        # On désactive le chargement réel des modèles lourds pour ce test d'intégration rapide
        cls.system.content_analyzer = MagicMock() 
        cls.system.source_verifier = MagicMock()
        cls.system.ontology_manager = MagicMock()

    def test_full_analysis_aggregation(self):
        """
        Test: Vérifie que le système agrège correctement les sous-scores
        pour produire un résultat final cohérent.
        """
        print("\n[Test Intégration] Simulation d'une analyse complète d'URL...")
        url = "http://test-news.com/article123"
        
        # 1. Configuration des Mocks pour les sous-systèmes
        
        # Mock du contenu extrait (scraper)
        self.system.scraper = MagicMock()
        self.system.scraper.extract_content.return_value = {
            'text': "Ceci est le texte de l'article.",
            'title': "Titre de l'article",
            'domain': "test-news.com"
        }
        
        # Mock des scores NLP (Système 1)
        self.system.content_analyzer.get_coherence_score.return_value = 0.85
        self.system.content_analyzer.get_bias_score.return_value = (0.2, 'Neutral')
        self.system.content_analyzer.analyze_sentiment.return_value = {'compound': 0.1} # Neutre
        self.system.content_analyzer.extract_claims.return_value = ["Affirmation 1"]

        # Mock des scores Symboliques (Système 2)
        self.system.source_verifier.assess_source_reputation.return_value = (0.75, {'reason': 'Simulation'})
        self.system.source_verifier.verify_claim_factuality.return_value = {'score': 0.5, 'evidence': {'found': False}}
        
        # Mock de l'ontologie
        self.system.ontology_manager.reason_and_get_score.return_value = 0.60

        # 2. Exécution de l'analyse complète
        result = self.system.analyze_url(url)

        # 3. Vérifications
        print(f"   -> Résultat final de l'agrégation : {result['final_score']:.2f}")
        
        self.assertIn('final_score', result)
        self.assertIn('details', result)
        # Le score final devrait être une moyenne pondérée des entrées.
        # Avec ces mocks (coherence=0.85, reputation=0.75, factcheck=0.5, onto=0.6), 
        # le score devrait être raisonnablement au-dessus de la neutralité.
        self.assertGreater(result['final_score'], 0.55, "Le score agrégé pour des entrées positives devrait être > 0.55")
        self.assertLess(result['final_score'], 0.9, "Le score ne devrait pas être parfait sans preuves absolues.")
        
        # Vérifier que les sous-scores sont bien présents dans les détails
        self.assertEqual(result['details']['nlp']['coherence'], 0.85)
        self.assertEqual(result['details']['source']['reputation_score'], 0.75)


if __name__ == '__main__':
    # Configuration pour une sortie de test plus propre
    unittest.main(verbosity=2)