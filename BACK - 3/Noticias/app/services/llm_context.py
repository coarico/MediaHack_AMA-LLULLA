import json
import re

from app.schemas.news import ExtractedArticle, LlmCompactContext, VerifiableClaim
from app.services.keyword_extractor import extract_keywords


MAX_TOP_SENTENCES = 8
MAX_SENTENCE_CHARS = 260
MAX_CLAIMS = 8


def build_llm_compact_context(
    article: ExtractedArticle,
    candidate_claims: list[VerifiableClaim] | None = None,
) -> LlmCompactContext:
    keywords = extract_keywords(article)
    top_sentences = _select_top_sentences(article, keywords)
    claims = [claim.claim for claim in (candidate_claims or [])][:MAX_CLAIMS]
    if not claims:
        claims = top_sentences[:4]

    compact_payload = {
        "title": article.title,
        "source_domain": article.source_domain,
        "published_at": article.published_at,
        "keywords": keywords[:12],
        "top_sentences": top_sentences,
        "candidate_claims": claims,
    }
    compact_text = json.dumps(compact_payload, ensure_ascii=False, separators=(",", ":"))
    original_chars = len(article.text or "")
    compact_chars = len(compact_text)

    compression_ratio = round(compact_chars / original_chars, 4) if original_chars else 1
    return LlmCompactContext(
        title=article.title,
        source_domain=article.source_domain,
        published_at=article.published_at,
        keywords=keywords[:12],
        top_sentences=top_sentences,
        candidate_claims=claims,
        original_text_chars=original_chars,
        compact_text_chars=compact_chars,
        estimated_tokens=max(1, round(compact_chars / 4)),
        compression_ratio=min(1, compression_ratio),
    )


def compact_context_to_prompt(context: LlmCompactContext) -> str:
    return json.dumps(context.model_dump(), ensure_ascii=False, indent=2)


def _select_top_sentences(article: ExtractedArticle, keywords: list[str]) -> list[str]:
    sentences = _split_sentences(article.text or "")
    scored = []
    normalized_keywords = [_normalize(keyword) for keyword in keywords]
    title_terms = set(_normalize(article.title or "").split())

    for index, sentence in enumerate(sentences):
        clean = re.sub(r"\s+", " ", sentence).strip()
        if len(clean) < 35:
            continue
        normalized = _normalize(clean)
        score = 0
        score += sum(4 for keyword in normalized_keywords if keyword and keyword in normalized)
        score += sum(1 for term in title_terms if len(term) > 3 and term in normalized)
        if re.search(r"\b\d+(?:[.,]\d+)?\s?%?\b", clean):
            score += 5
        if any(word in normalized for word in ["denuncio", "denunció", "afirmo", "afirmó", "aseguro", "aseguró", "expreso", "expresó", "anuncio", "anunció"]):
            score += 4
        if index < 4:
            score += 2
        scored.append((score, index, clean[:MAX_SENTENCE_CHARS]))

    if not scored:
        fallback = re.sub(r"\s+", " ", article.text or "").strip()
        return [fallback[:MAX_SENTENCE_CHARS]] if fallback else []

    selected = sorted(scored, key=lambda item: (-item[0], item[1]))[:MAX_TOP_SENTENCES]
    return [sentence for _, _, sentence in sorted(selected, key=lambda item: item[1])]


def _split_sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+", text)


def _normalize(value: str) -> str:
    replacements = str.maketrans("áéíóúñÁÉÍÓÚÑ", "aeiounAEIOUN")
    return value.translate(replacements).lower()
