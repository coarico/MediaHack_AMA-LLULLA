"""
Research classification and evidence hierarchy management.

This module categorizes research queries and determines the appropriate
evidence hierarchy based on the type of information being sought.
"""

import json
import re
from functools import lru_cache
from pathlib import Path


HIERARCHY_FILE = Path(__file__).resolve().parents[2] / "data" / "evidence_hierarchy.json"


class ResearchClassifier:
    """Classify queries and manage evidence hierarchy."""

    def __init__(self):
        self.hierarchy = self._load_hierarchy()

    @lru_cache(maxsize=1)
    def _load_hierarchy(self) -> dict:
        """Load evidence hierarchy configuration."""
        if not HIERARCHY_FILE.exists():
            return {}
        try:
            with HIERARCHY_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def classify_query(self, query: str, topic: str = "", claims: list | None = None) -> dict:
        """
        Classify a query to determine research category and evidence priority.

        Args:
            query: The user's question or search query
            topic: The main topic/article subject
            claims: List of extracted claims (optional)

        Returns:
            Dict with category, confidence, and recommended hierarchy order
        """
        combined_text = f"{query} {topic}".lower()
        claims_text = " ".join([c.get("claim", "") for c in (claims or [])]).lower()
        all_text = f"{combined_text} {claims_text}".lower()

        category = self._detect_category(all_text)
        confidence = self._calculate_confidence(all_text, category)
        strategy = self.hierarchy.get("query_category_strategies", {}).get(
            category, 
            self.hierarchy.get("query_category_strategies", {}).get("general", {})
        )

        return {
            "category": category,
            "confidence": confidence,
            "hierarchy_order": strategy.get("order", [6, 3, 7, 5, 4, 8]),
            "primary_operators": strategy.get("primary_operators", []),
            "description": strategy.get("description", ""),
            "keywords_matched": self._match_keywords(all_text, strategy.get("keywords", [])),
        }

    def _detect_category(self, text: str) -> str:
        """Detect the primary research category from text."""
        strategies = self.hierarchy.get("query_category_strategies", {})
        
        # Check for desinformation/fact-check signals first (highest specificity)
        factcheck_keywords = ["es verdad", "verificar", "desinformación", "viral", "fake", "falso", "comprueba", "¿verdad", "afirma"]
        if any(kw in text for kw in factcheck_keywords):
            return "factcheck_desinformation"

        # Constitutional questions
        constitutional_keywords = ["constitución", "derecho", "garantía", "debido proceso", "inconstitucional"]
        if any(kw in text for kw in constitutional_keywords):
            return "constitutional"

        # Legal questions
        legal_keywords = ["ley", "decreto", "norma", "reglamento", "acuerdo", "resolución", "legislación"]
        if any(kw in text for kw in legal_keywords):
            return "legal"

        # Electoral questions (check before political/statistical to take priority)
        electoral_keywords = ["elección", "elecciones", "voto", "candidato", "comicio", "electoral", "postulant"]
        if any(kw in text for kw in electoral_keywords):
            return "electoral"

        # Political questions
        political_keywords = ["política", "gobierno", "ministro", "diputado", "congreso", "parlamento", "voto"]
        if any(kw in text for kw in political_keywords):
            return "political"

        # Economic questions
        economic_keywords = ["economía", "inflación", "pib", "presupuesto", "tasa", "cambio", "finanzas", "bolsa"]
        if any(kw in text for kw in economic_keywords):
            return "economic"

        # Statistical/data questions
        statistical_keywords = ["porcentaje", "cifra", "estadística", "cuántos", "cuánta", "cuántos", "dato", "número", "%"]
        if any(kw in text for kw in statistical_keywords):
            return "statistical"

        # Security questions
        security_keywords = ["seguridad", "delito", "crimen", "violencia", "orden público", "policía", "crimen"]
        if any(kw in text for kw in security_keywords):
            return "security"

        # Health questions
        health_keywords = ["salud", "enfermedad", "vacuna", "epidemia", "sanitario", "médico", "hospital", "covid"]
        if any(kw in text for kw in health_keywords):
            return "health"

        # Education questions
        education_keywords = ["educación", "escuela", "universidad", "alumno", "docente", "profesor", "académico"]
        if any(kw in text for kw in education_keywords):
            return "education"

        # Labor questions
        labor_keywords = ["empleo", "desempleo", "salario", "trabajador", "laboral", "sindical", "huelga"]
        if any(kw in text for kw in labor_keywords):
            return "labor"

        # Current news/events (recent, today, now)
        news_keywords = ["hoy", "ahora", "reciente", "acontecimiento", "noticia", "última hora", "últimas noticias"]
        if any(kw in text for kw in news_keywords):
            return "news_current_events"

        return "general"

    def _calculate_confidence(self, text: str, category: str) -> float:
        """Calculate confidence in category classification (0.0-1.0)."""
        strategy = self.hierarchy.get("query_category_strategies", {}).get(category, {})
        keywords = strategy.get("keywords", [])
        
        if not keywords:
            return 0.5  # Low confidence for general category
        
        matches = sum(1 for kw in keywords if kw.lower() in text)
        return min(0.95, 0.5 + (matches / len(keywords)) * 0.45)

    def _match_keywords(self, text: str, keywords: list) -> list:
        """Find which keywords matched in the text."""
        return [kw for kw in keywords if kw.lower() in text]

    def get_hierarchy_order(self, category: str) -> list:
        """Get evidence level search order for a category (0-8)."""
        strategy = self.hierarchy.get("query_category_strategies", {}).get(category)
        if not strategy:
            return [6, 3, 7, 5, 4, 8]  # Default: media -> institutions -> verify
        return strategy.get("order", [6, 3, 7, 5, 4, 8])

    def get_primary_operators(self, category: str) -> list:
        """Get primary site: operators for fastest source identification."""
        strategy = self.hierarchy.get("query_category_strategies", {}).get(category)
        if not strategy:
            return []
        return strategy.get("primary_operators", [])

    def get_sources_by_level(self, level: int) -> list:
        """Get all sources at a specific evidence level (0-8)."""
        level_key = f"level_{level}_"
        
        # Find matching level key
        for key in self.hierarchy.get("evidence_hierarchy", {}).keys():
            if key.startswith(level_key):
                level_data = self.hierarchy["evidence_hierarchy"][key]
                return level_data.get("sources", [])
        
        return []

    def get_search_operators_for_level(self, level: int) -> list:
        """Get Google site: operators for a specific evidence level."""
        level_key = f"level_{level}_"
        
        for key in self.hierarchy.get("evidence_hierarchy", {}).keys():
            if key.startswith(level_key):
                level_data = self.hierarchy["evidence_hierarchy"][key]
                return level_data.get("search_operators", [])
        
        return []

    def get_evidence_level(self, source_domain: str) -> int | None:
        """
        Determine the evidence level (0-8) of a source by domain.

        Returns None if source not found in hierarchy.
        """
        domain = source_domain.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]

        for i in range(9):  # Levels 0-8
            level_key = f"level_{i}_"
            for key in self.hierarchy.get("evidence_hierarchy", {}).keys():
                if key.startswith(level_key):
                    level_data = self.hierarchy["evidence_hierarchy"][key]
                    for source in level_data.get("sources", []):
                        source_domain_normalized = source.get("domain", "").lower()
                        if (
                            domain == source_domain_normalized
                            or domain.endswith(f".{source_domain_normalized}")
                            or source_domain_normalized in domain
                        ):
                            return i
        
        return None

    def is_primary_source(self, source_domain: str) -> bool:
        """Check if a source is a primary source (level 0-3)."""
        level = self.get_evidence_level(source_domain)
        return level is not None and level <= 3

    def is_official_source(self, source_domain: str) -> bool:
        """Check if a source is an official institution (level 0-4)."""
        level = self.get_evidence_level(source_domain)
        return level is not None and level <= 4

    def get_level_name(self, level: int) -> str:
        """Get the human-readable name for an evidence level."""
        level_key = f"level_{level}_"
        
        for key in self.hierarchy.get("evidence_hierarchy", {}).keys():
            if key.startswith(level_key):
                level_data = self.hierarchy["evidence_hierarchy"][key]
                return level_data.get("name", f"Nivel {level}")
        
        return f"Nivel {level}"

    def build_hierarchical_search_query(
        self,
        base_query: str,
        category: str,
        max_levels: int = 3
    ) -> list[dict]:
        """
        Build a list of search queries ordered by evidence hierarchy.

        Args:
            base_query: The base search query
            category: Query category for hierarchy determination
            max_levels: Maximum number of levels to search

        Returns:
            List of {"query": str, "level": int, "level_name": str, "primary": bool} ordered by priority
        """
        hierarchy_order = self.get_hierarchy_order(category)
        search_queries = []

        for level in hierarchy_order[:max_levels]:
            operators = self.get_search_operators_for_level(level)
            
            if operators:
                for operator in operators:
                    # Build search: site:domain base_query
                    query = f"{operator} {base_query}"
                    search_queries.append({
                        "query": query,
                        "level": level,
                        "level_name": self.get_level_name(level),
                        "operator": operator,
                        "primary": level <= 3,
                    })
            else:
                # No specific operators for this level, use base query
                search_queries.append({
                    "query": base_query,
                    "level": level,
                    "level_name": self.get_level_name(level),
                    "operator": None,
                    "primary": level <= 3,
                })

        return search_queries

    def get_source_priority_ranking(self, sources: list[dict]) -> list[dict]:
        """
        Rank a list of sources by evidence hierarchy level.

        Args:
            sources: List of sources with 'url' or 'source' key

        Returns:
            Same list, sorted by evidence level (lowest number first)
        """
        ranked = []
        
        for source in sources:
            domain = source.get("url") or source.get("source") or ""
            if "://" in domain:
                domain = domain.split("://")[1].split("/")[0]
            
            level = self.get_evidence_level(domain)
            ranked.append(({
                **source,
                "evidence_level": level if level is not None else 99,
                "is_primary": level is not None and level <= 3,
            }))
        
        ranked.sort(key=lambda x: x.get("evidence_level", 99))
        return ranked


# Singleton instance
_classifier = None


def get_research_classifier() -> ResearchClassifier:
    """Get or create the singleton ResearchClassifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = ResearchClassifier()
    return _classifier
