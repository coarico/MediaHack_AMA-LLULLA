"""
Integration test for evidence hierarchy in kuybot system.
"""

import pytest
from app.services.research_classifier import get_research_classifier
from app.services.kuybot import (
    _determine_research_strategy,
    _build_hierarchical_search_query,
    _extract_official_sources,
)


class TestEvidenceHierarchyIntegration:
    """Integration tests for evidence hierarchy with kuybot."""

    def test_legal_query_strategy(self):
        """Test that legal queries get the correct research strategy."""
        payload = {
            "question": "¿Qué dice la nueva ley de educación?",
            "news": {
                "title": "Nueva ley aprobada",
                "verifiable_claims": [],
                "related_news": []
            }
        }
        
        strategy = _determine_research_strategy(payload)
        assert strategy["category"] == "legal"
        assert strategy["hierarchy_order"][0] in [0, 1, 2]  # Legal sources first

    def test_electoral_query_strategy(self):
        """Test that electoral queries get correct strategy."""
        payload = {
            "question": "¿Cuántos candidatos se inscribieron?",
            "news": {
                "title": "Elecciones 2026",
                "verifiable_claims": [],
                "related_news": []
            }
        }
        
        strategy = _determine_research_strategy(payload)
        assert strategy["category"] == "electoral"
        # Electoral should prioritize CNE (level 3)
        assert 3 in strategy["hierarchy_order"]

    def test_statistical_query_strategy(self):
        """Test that statistical queries prioritize data sources."""
        payload = {
            "question": "¿Cuál es el porcentaje de desempleo?",
            "news": {
                "title": "Estadísticas económicas",
                "verifiable_claims": [],
                "related_news": []
            }
        }
        
        strategy = _determine_research_strategy(payload)
        assert strategy["category"] == "statistical"
        # Statistical should have institutions/data in hierarchy
        assert 3 in strategy["hierarchy_order"] or 4 in strategy["hierarchy_order"]

    def test_hierarchical_search_query_building(self):
        """Test building hierarchical search queries."""
        payload = {
            "question": "¿Es verdad que los salarios aumentarán?",
            "news": {
                "title": "Propuesta de aumento",
                "verifiable_claims": [],
                "related_news": [],
                "main_claims": ["Salarios aumentarán 15%"],
                "summary": "Nueva propuesta de política salarial"
            }
        }
        
        queries = _build_hierarchical_search_query(payload, max_levels=2)
        
        assert len(queries) > 0
        # First queries should be from primary sources
        first_queries = queries[:3]
        primary_count = sum(1 for q in first_queries if q.get("primary", False))
        assert primary_count > 0

    def test_official_sources_extraction_respects_hierarchy(self):
        """Test that official sources extraction respects evidence hierarchy."""
        payload = {
            "news": {
                "related_news": [
                    {
                        "title": "CNE statement",
                        "url": "https://cne.gob.ec/news/123",
                        "source": "CNE",
                        "source_type": "institucion"
                    },
                    {
                        "title": "El Universo coverage",
                        "url": "https://eluniverso.com/news/456",
                        "source": "El Universo",
                        "source_type": "medio_radar"
                    },
                    {
                        "title": "INEC data",
                        "url": "https://inec.gob.ec/data/789",
                        "source": "INEC",
                        "source_type": "institucion"
                    }
                ]
            }
        }
        
        officials = _extract_official_sources(payload)
        
        # Should return sources in priority order
        assert len(officials) > 0
        
        # First sources should be institutional (lower evidence level)
        first_sources = [o for o in officials[:2]]
        has_institutional = any("CNE" in o.get("source", "") or "INEC" in o.get("source", "") for o in first_sources)
        assert has_institutional

    def test_primary_source_priority(self):
        """Test that primary sources (level 0-3) are found first."""
        classifier = get_research_classifier()
        
        # Level 0 source
        level_0 = classifier.get_evidence_level("registrooficial.gob.ec")
        assert level_0 == 0
        assert classifier.is_primary_source("registrooficial.gob.ec")
        
        # Level 3 source (institutional)
        level_3 = classifier.get_evidence_level("cne.gob.ec")
        assert level_3 == 3
        assert classifier.is_primary_source("cne.gob.ec")
        
        # Level 6 source (media - NOT primary)
        level_6 = classifier.get_evidence_level("eluniverso.com")
        assert level_6 == 6
        assert not classifier.is_primary_source("eluniverso.com")

    def test_category_confidence_improves_with_keywords(self):
        """Test that confidence increases with more matching keywords."""
        classifier = get_research_classifier()
        
        # Single keyword
        single = classifier.classify_query("ley")
        
        # Multiple keywords
        multiple = classifier.classify_query("nueva ley educación decreto")
        
        assert multiple["confidence"] >= single["confidence"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
