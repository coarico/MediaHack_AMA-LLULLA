import json
import unicodedata
from functools import lru_cache
from pathlib import Path

from app.schemas.news import ExtractedArticle, InformationRelevance, NewsAnalysis


TAXONOMY_FILE = Path(__file__).resolve().parents[2] / "data" / "election_taxonomy.json"
REQUIRES_ELECTORAL_CONTEXT = {"violencia_seguridad", "narcotrafico"}


def classify_information_relevance(article: ExtractedArticle, analysis: NewsAnalysis) -> InformationRelevance:
    taxonomy = _load_taxonomy()
    definition = taxonomy.get(
        "definition",
        "Informacion relevante electoral es contenido que puede afectar la comprension o decision ciudadana en elecciones.",
    )
    text = _normalize(
        " ".join(
            [
                article.title or "",
                analysis.topic,
                analysis.category,
                " ".join(analysis.keywords),
                " ".join(analysis.main_claims),
                article.text[:4000],
            ]
        )
    )

    election_terms = [
        "eleccion",
        "electoral",
        "voto",
        "votacion",
        "candidato",
        "campana",
        "campanas",
        "comicios",
        "urna",
        "escrutinio",
    ]
    direct_hits = [term for term in election_terms if term in text]

    matched_subtopics: list[str] = []
    reasons: list[str] = []
    for subtopic in taxonomy.get("subtopics", []):
        subtopic_id = subtopic.get("id", subtopic.get("label", "sin_id"))
        hits = [keyword for keyword in subtopic.get("keywords", []) if _normalize(keyword) in text]
        if hits and subtopic_id in REQUIRES_ELECTORAL_CONTEXT and not direct_hits:
            continue
        if hits:
            matched_subtopics.append(subtopic_id)
            reasons.append(f"{subtopic.get('label')}: coincide con {', '.join(hits[:4])}.")

    score = min(100, len(matched_subtopics) * 18 + len(direct_hits) * 8)
    if matched_subtopics and direct_hits:
        relation_type = "directa"
        domain = "electoral"
    elif matched_subtopics:
        relation_type = "indirecta"
        domain = "electoral"
    elif direct_hits:
        relation_type = "contextual"
        domain = "electoral"
        reasons.append(f"Se detectaron terminos electorales: {', '.join(direct_hits[:4])}.")
    else:
        relation_type = "no_relacionada"
        domain = "no_electoral"

    is_relevant = score >= 25 or bool(matched_subtopics)
    non_relevant_reason = None
    if not is_relevant:
        non_relevant_reason = "No se detectaron senales suficientes de relacion con elecciones o subtemas definidos."
        how_it_relates = "No se encontro una conexion suficiente con el proceso electoral ni con los subtemas configurados."
    elif relation_type == "directa":
        how_it_relates = "Se relaciona directamente porque menciona terminos electorales y subtemas configurados en la taxonomia."
    elif relation_type == "indirecta":
        how_it_relates = "Se relaciona indirectamente porque toca subtemas electorales aunque no use de forma clara lenguaje electoral general."
    else:
        how_it_relates = "Se relaciona de forma contextual porque contiene lenguaje electoral, pero requiere revisar si afecta decision, confianza o participacion ciudadana."

    return InformationRelevance(
        is_relevant=is_relevant,
        relevance_score=max(0, min(100, score)),
        domain=domain,
        definition_applied=definition,
        subtopics=matched_subtopics,
        relation_type=relation_type,
        reasons=reasons[:8],
        how_it_relates=how_it_relates,
        non_relevant_reason=non_relevant_reason,
    )


@lru_cache
def _load_taxonomy() -> dict:
    if not TAXONOMY_FILE.exists():
        return {}
    with TAXONOMY_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))
