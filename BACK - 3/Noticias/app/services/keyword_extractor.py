import re
import unicodedata

from app.schemas.news import ExtractedArticle


STOPWORDS = {
    "actualidad",
    "ademas",
    "ahora",
    "ante",
    "aunque",
    "cada",
    "comercio",
    "como",
    "con",
    "contra",
    "cuando",
    "desde",
    "donde",
    "durante",
    "entre",
    "esta",
    "estas",
    "este",
    "estos",
    "fue",
    "han",
    "hay",
    "las",
    "los",
    "mas",
    "para",
    "pero",
    "por",
    "porque",
    "que",
    "segun",
    "sin",
    "sobre",
    "tambien",
    "tras",
    "una",
    "uno",
    "unos",
    "del",
    "noticia",
    "noticias",
    "publica",
    "publico",
    "publicos",
    "via",
    "video",
    "audio",
}

DOMAIN_PHRASES = {
    "seguridad vial": ("seguridad", "vial"),
    "transito": ("transito", "transito"),
    "movilidad": ("movilidad", "movilidad"),
    "inseguridad": ("inseguridad", "inseguridad"),
    "violencia": ("violencia", "violencia"),
    "elecciones": ("elecciones", "elecciones"),
    "fraude electoral": ("fraude", "electoral"),
    "narcotrafico": ("narcotrafico", "narcotrafico"),
}


def extract_keywords(article: ExtractedArticle, limit: int = 12) -> list[str]:
    title = article.title or ""
    body = article.text or ""
    weighted_text = " ".join([title, title, title, body])
    scored: dict[str, float] = {}
    display: dict[str, str] = {}

    for phrase in _title_phrases(title):
        key = _normalize(phrase)
        if key and key not in STOPWORDS:
            scored[key] = scored.get(key, 0) + 14
            display[key] = phrase

    for token in _tokens(weighted_text):
        key = _normalize(token)
        if len(key) < 4 or key in STOPWORDS:
            continue
        scored[key] = scored.get(key, 0) + (3 if token in title else 1)
        display.setdefault(key, _clean_display(token))

    normalized_text = _normalize(weighted_text)
    for label, required_terms in DOMAIN_PHRASES.items():
        if all(term in normalized_text for term in required_terms):
            scored[label] = scored.get(label, 0) + 5
            display[label] = label

    return [
        display[key]
        for key, _ in sorted(scored.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def infer_category_from_keywords(keywords: list[str], fallback: str = "noticias") -> str:
    text = " ".join(_normalize(keyword) for keyword in keywords)
    if any(term in text for term in ("transito", "movilidad", "seguridad vial", "avenida", "conductores")):
        return "seguridad/movilidad"
    if any(term in text for term in ("inseguridad", "violencia", "policial", "cadaveres")):
        return "seguridad"
    if any(term in text for term in ("elecciones", "electoral", "votos", "cne")):
        return "politica/electoral"
    return fallback


def merge_keywords(primary: list[str], secondary: list[str], limit: int = 12) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for keyword in [*primary, *secondary]:
        key = _normalize(keyword)
        if not key or key in seen or _is_weak_keyword(key):
            continue
        seen.add(key)
        merged.append(keyword)
        if len(merged) >= limit:
            break
    return merged


def _title_phrases(title: str) -> list[str]:
    phrases: list[str] = []
    for match in re.finditer(r"\b[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚáéíóúÑñ]+(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚáéíóúÑñ]+)+", title):
        phrase = _clean_display(match.group(0))
        if len(phrase) <= 45:
            phrases.append(phrase)
    return phrases


def _tokens(text: str) -> list[str]:
    return re.findall(r"\b[\wÁÉÍÓÚáéíóúÑñ]{3,}\b", text)


def _clean_display(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" .,;:()[]{}\"'")).strip()


def _normalize(value: str) -> str:
    clean = unicodedata.normalize("NFKD", value.lower())
    clean = "".join(char for char in clean if not unicodedata.combining(char))
    clean = re.sub(r"[^\w\s/-]", " ", clean)
    return re.sub(r"\s+", " ", clean).strip()


def _is_weak_keyword(key: str) -> bool:
    tokens = key.split()
    if key in STOPWORDS:
        return True
    return bool(tokens) and all(token in STOPWORDS for token in tokens)
