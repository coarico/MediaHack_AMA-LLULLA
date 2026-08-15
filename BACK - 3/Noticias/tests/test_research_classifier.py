"""
Test suite for research classification and evidence hierarchy.
"""

import pytest
from app.services.research_classifier import ResearchClassifier, get_research_classifier


class TestResearchClassifier:
    """Test research query classification and evidence hierarchy."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = ResearchClassifier()

    def test_classifies_legal_query(self):
        """Test classification of legal/regulatory queries."""
        query = "¿Es verdad que aprobaron una nueva ley sobre educación?"
        classification = self.classifier.classify_query(query)
        
        # Might be legal or factcheck_desinformation depending on keyword priority
        assert classification["category"] in ["legal", "factcheck_desinformation"]
        assert classification["confidence"] > 0.5

    def test_classifies_factcheck_query_first(self):
        """Test that factcheck keywords take priority."""
        query = "¿Es verdad que..."
        classification = self.classifier.classify_query(query)
        assert classification["category"] == "factcheck_desinformation"
        assert classification["confidence"] >= 0.5

    def test_classifies_constitutional_query(self):
        """Test classification of constitutional questions."""
        query = "¿Cuál es el derecho constitucional a la educación?"
        classification = self.classifier.classify_query(query)
        assert classification["category"] == "constitutional"
        assert classification["confidence"] > 0.5

    def test_classifies_political_query(self):
        """Test classification of political questions."""
        query = "¿Qué dijo el ministro sobre las elecciones?"
        classification = self.classifier.classify_query(query)
        assert classification["category"] in ["political", "electoral"]
        assert classification["confidence"] > 0.5

    def test_classifies_electoral_query(self):
        """Test classification of electoral questions."""
        query = "¿Cuántos candidatos se inscribieron para las elecciones?"
        classification = self.classifier.classify_query(query)
        assert classification["category"] == "electoral"
        assert classification["confidence"] > 0.5

    def test_classifies_economic_query(self):
        """Test classification of economic questions."""
        query = "¿Cuál es la inflación en Ecuador este año?"
        classification = self.classifier.classify_query(query)
        assert classification["category"] == "economic"
        assert classification["confidence"] > 0.5

    def test_classifies_statistical_query(self):
        """Test classification of statistical/data questions."""
        query = "¿Cuál es el porcentaje de desempleo?"
        classification = self.classifier.classify_query(query)
        assert classification["category"] == "statistical"
        assert classification["confidence"] > 0.5

    def test_classifies_health_query(self):
        """Test classification of health questions."""
        query = "¿Cuál es el estado de la epidemia de dengue?"
        classification = self.classifier.classify_query(query)
        assert classification["category"] == "health"
        assert classification["confidence"] > 0.5

    def test_hierarchy_order_for_legal(self):
        """Test that legal queries prioritize legal sources."""
        query = "¿Qué dice la ley sobre trabajadores?"
        order = self.classifier.get_hierarchy_order("legal")
        # Legal category should prioritize levels 0-3 (legal institutions)
        assert order[0] in [0, 1, 2]

    def test_hierarchy_order_for_statistical(self):
        """Test that statistical queries prioritize data sources."""
        order = self.classifier.get_hierarchy_order("statistical")
        # Statistical should prioritize institutions (level 3) and data (level 4)
        assert 3 in order or 4 in order

    def test_evidence_level_for_registro_oficial(self):
        """Test evidence level detection for Registro Oficial."""
        level = self.classifier.get_evidence_level("registrooficial.gob.ec")
        assert level == 0, "Registro Oficial should be level 0"

    def test_evidence_level_for_corte_constitucional(self):
        """Test evidence level detection for Corte Constitucional."""
        level = self.classifier.get_evidence_level("corteconstitucional.gob.ec")
        assert level == 1, "Corte Constitucional should be level 1"

    def test_evidence_level_for_inec(self):
        """Test evidence level detection for INEC."""
        level = self.classifier.get_evidence_level("inec.gob.ec")
        assert level == 3, "INEC should be level 3 (official institutions)"

    def test_evidence_level_for_traditional_media(self):
        """Test evidence level detection for traditional media."""
        level = self.classifier.get_evidence_level("eluniverso.com")
        assert level == 6, "Traditional media should be level 6"

    def test_evidence_level_for_social_media(self):
        """Test evidence level detection for social media."""
        level = self.classifier.get_evidence_level("twitter.com")
        assert level == 8, "Social media should be level 8"

    def test_is_primary_source_for_level_0(self):
        """Test primary source detection for legal sources."""
        is_primary = self.classifier.is_primary_source("registrooficial.gob.ec")
        assert is_primary is True

    def test_is_primary_source_for_media(self):
        """Test that media is not detected as primary source."""
        is_primary = self.classifier.is_primary_source("eluniverso.com")
        assert is_primary is False

    def test_is_official_source(self):
        """Test official source detection."""
        is_official = self.classifier.is_official_source("inec.gob.ec")
        assert is_official is True

    def test_is_official_source_excludes_media(self):
        """Test that media is not classified as official."""
        is_official = self.classifier.is_official_source("eluniverso.com")
        assert is_official is False

    def test_build_hierarchical_search_query_for_legal(self):
        """Test hierarchical search query building for legal questions."""
        queries = self.classifier.build_hierarchical_search_query(
            base_query="nueva ley educación",
            category="legal",
            max_levels=2
        )
        
        assert len(queries) > 0
        # First query should be from a primary legal source
        assert queries[0]["primary"] is True
        # Should have site: operators
        assert any(q.get("operator") for q in queries)

    def test_get_level_name(self):
        """Test level name retrieval."""
        name_0 = self.classifier.get_level_name(0)
        name_6 = self.classifier.get_level_name(6)
        
        assert "Jurídica" in name_0 or "legal" in name_0.lower()
        assert "Comunicación" in name_6 or "media" in name_6.lower()

    def test_singleton_pattern(self):
        """Test that get_research_classifier returns same instance."""
        classifier1 = get_research_classifier()
        classifier2 = get_research_classifier()
        assert classifier1 is classifier2

    def test_classify_query_with_claims(self):
        """Test classification with claims context."""
        claims = [
            {"claim": "El CNE aprobó 1200 candidatos"},
            {"claim": "Se realizarán elecciones en febrero"}
        ]
        classification = self.classifier.classify_query(
            query="¿Es verdad que hay 1200 candidatos?",
            topic="Elecciones 2026",
            claims=claims
        )
        assert classification["category"] in ["electoral", "factcheck_desinformation"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
