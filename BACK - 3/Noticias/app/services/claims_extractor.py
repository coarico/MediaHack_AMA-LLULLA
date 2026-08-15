import re

from app.schemas.news import ExtractedArticle, VerifiableClaim


QUOTE_RE = re.compile(r'"([^"]{20,220})"')
PERCENT_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?%")
DATE_HINT_RE = re.compile(r"\b(?:lunes|martes|miercoles|miércoles|jueves|viernes|sabado|sábado|domingo|\d{1,2}/\d{1,2}/\d{2,4})\b", re.IGNORECASE)
ACCUSATION_HINTS = ("acuso", "acusó", "denuncio", "denunció", "fraude", "corrupcion", "corrupción")


def extract_verifiable_claims(article: ExtractedArticle, max_claims: int = 8) -> list[VerifiableClaim]:
    claims: list[VerifiableClaim] = []
    sentences = _split_sentences(article.text)

    for sentence in sentences:
        clean = sentence.strip()
        if len(clean) < 40:
            continue

        claim_type = _classify_sentence(clean)
        if claim_type:
            claims.append(
                VerifiableClaim(
                    claim=clean[:500],
                    type=claim_type,
                    entities=_guess_entities(clean),
                    needs_external_verification=True,
                )
            )
        if len(claims) >= max_claims:
            break

    for quote in QUOTE_RE.findall(article.text):
        if len(claims) >= max_claims:
            break
        claims.append(
            VerifiableClaim(
                claim=quote.strip(),
                type="cita",
                entities=_guess_entities(quote),
                needs_external_verification=True,
            )
        )

    return _dedupe_claims(claims)[:max_claims]


def _classify_sentence(sentence: str):
    lowered = sentence.lower()
    if PERCENT_RE.search(sentence) or re.search(r"\b\d{2,}\b", sentence):
        return "estadistica"
    if DATE_HINT_RE.search(sentence):
        return "fecha"
    if any(hint in lowered for hint in ACCUSATION_HINTS):
        return "acusacion"
    if any(verb in lowered for verb in ["aprob", "anuncio", "confirm", "ocurr", "realiz"]):
        return "evento"
    return None


def _split_sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+", text)


def _guess_entities(sentence: str) -> list[str]:
    return re.findall(r"\b[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+){0,2}", sentence)[:6]


def _dedupe_claims(claims: list[VerifiableClaim]) -> list[VerifiableClaim]:
    seen: set[str] = set()
    deduped: list[VerifiableClaim] = []
    for claim in claims:
        key = claim.claim.lower()[:120]
        if key not in seen:
            seen.add(key)
            deduped.append(claim)
    return deduped

