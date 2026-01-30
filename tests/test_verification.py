#!/usr/bin/env python3
"""
Tests unitaires pour le système de vérification SysCRED

Auteur: Dominique S. Loyer
"""

import pytest
from syscred import CredibilityVerificationSystem


class TestSystemInitialization:
    """Tests d'initialisation du système"""
    
    def test_system_initialization(self):
        """Test que le système s'initialise correctement"""
        system = CredibilityVerificationSystem()
        assert system is not None
        
    def test_system_has_verify_method(self):
        """Test que le système a la méthode verify_information"""
        system = CredibilityVerificationSystem()
        assert hasattr(system, 'verify_information')
        assert callable(getattr(system, 'verify_information'))


class TestURLVerification:
    """Tests de vérification d'URL"""
    
    def test_verify_url_returns_dict(self):
        """Test que la vérification d'URL retourne un dictionnaire"""
        system = CredibilityVerificationSystem()
        result = system.verify_information("https://www.bbc.com")
        assert isinstance(result, dict)
    
    def test_verify_url_has_score(self):
        """Test que le résultat contient un score"""
        system = CredibilityVerificationSystem()
        result = system.verify_information("https://www.bbc.com")
        
        assert "scoreCredibilite" in result
        assert isinstance(result["scoreCredibilite"], (int, float))
    
    def test_verify_url_score_range(self):
        """Test que le score est entre 0 et 1"""
        system = CredibilityVerificationSystem()
        result = system.verify_information("https://www.bbc.com")
        
        score = result["scoreCredibilite"]
        assert 0 <= score <= 1, f"Score {score} hors limites [0,1]"
    
    def test_verify_url_has_level(self):
        """Test que le résultat contient un niveau de crédibilité"""
        system = CredibilityVerificationSystem()
        result = system.verify_information("https://www.bbc.com")
        
        assert "niveauCredibilite" in result
        assert result["niveauCredibilite"] in ["HIGH", "MEDIUM", "LOW"]


class TestTextVerification:
    """Tests de vérification de texte"""
    
    def test_verify_text_returns_dict(self):
        """Test que la vérification de texte retourne un dictionnaire"""
        system = CredibilityVerificationSystem()
        text = "This is a test statement about research findings."
        result = system.verify_information(text)
        
        assert isinstance(result, dict)
    
    def test_verify_text_has_required_fields(self):
        """Test que le résultat contient les champs requis"""
        system = CredibilityVerificationSystem()
        text = "According to researchers, this study shows results."
        result = system.verify_information(text)
        
        assert "scoreCredibilite" in result
        assert "niveauCredibilite" in result
    
    def test_verify_text_level_valid(self):
        """Test que le niveau est valide"""
        system = CredibilityVerificationSystem()
        text = "The data suggests a significant correlation."
        result = system.verify_information(text)
        
        assert result["niveauCredibilite"] in ["HIGH", "MEDIUM", "LOW"]


class TestCredibilityLevels:
    """Tests des niveaux de crédibilité"""
    
    def test_high_score_gives_high_level(self):
        """Test qu'un score élevé donne un niveau HIGH"""
        system = CredibilityVerificationSystem()
        # Utiliser une source connue fiable
        result = system.verify_information("https://www.nature.com")
        
        if result["scoreCredibilite"] >= 0.7:
            assert result["niveauCredibilite"] == "HIGH"
    
    def test_low_score_gives_low_level(self):
        """Test qu'un score bas donne un niveau LOW"""
        system = CredibilityVerificationSystem()
        # Texte vague sans source
        text = "Someone said something somewhere."
        result = system.verify_information(text)
        
        if result["scoreCredibilite"] < 0.4:
            assert result["niveauCredibilite"] == "LOW"


class TestErrorHandling:
    """Tests de gestion des erreurs"""
    
    def test_empty_string_handling(self):
        """Test que le système gère les chaînes vides"""
        system = CredibilityVerificationSystem()
        # Ne devrait pas planter
        result = system.verify_information("")
        assert isinstance(result, dict)
    
    def test_none_input_handling(self):
        """Test que le système gère None"""
        system = CredibilityVerificationSystem()
        # Devrait lever une exception ou retourner un résultat par défaut
        with pytest.raises((TypeError, ValueError, AttributeError)):
            system.verify_information(None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
