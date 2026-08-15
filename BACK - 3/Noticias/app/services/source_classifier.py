import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from app.schemas.news import SourceClassification


RADAR_FILE = Path(__file__).resolve().parents[2] / "data" / "radar_media.json"
SOURCE_REGISTRY_FILE = Path(__file__).resolve().parents[2] / "data" / "source_registry.json"

SOCIAL_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "x.com",
    "twitter.com",
    "tiktok.com",
    "threads.net",
    "linkedin.com",
}
VIDEO_DOMAINS = {"youtube.com", "youtu.be", "vimeo.com", "twitch.tv"}
GOV_HINTS = (".gov", ".gob", "gov.", "gob.")
ORG_HINTS = (".org",)
NEWS_HINTS = (
    "news",
    "noticias",
    "diario",
    "periodico",
    "radio",
    "tv",
    "canal",
    "prensa",
    "journal",
)
BLOG_HINTS = ("blog", "substack.com", "medium.com", "wordpress.com", "blogspot.com")


def classify_source(url: str, source_domain: str | None = None) -> SourceClassification:
    domain = _normalize_domain(source_domain or urlparse(url).netloc)
    handle = _extract_handle(url)
    radar_match = _match_radar_media(domain)
    if radar_match:
        return SourceClassification(
            is_radar_media=True,
            communication_type="medio_radar",
            source_name=radar_match.get("name"),
            matched_domain=radar_match.get("domain"),
            matched_handle=None,
            registry_category=radar_match.get("category"),
            editorial_alignment=radar_match.get("editorial_alignment"),
            platform=radar_match.get("platform"),
            verification_network=radar_match.get("verification_network"),
            confidence=1.0,
            explanation="El dominio coincide con la lista Radar configurada.",
        )

    registry_match = _match_source_registry(domain, handle)
    if registry_match:
        return SourceClassification(
            is_radar_media=False,
            communication_type=registry_match.get("communication_type", "medio_no_radar"),
            source_name=registry_match.get("name"),
            matched_domain=registry_match.get("domain"),
            matched_handle=registry_match.get("handle"),
            registry_category=registry_match.get("category"),
            editorial_alignment=registry_match.get("editorial_alignment"),
            platform=registry_match.get("platform"),
            verification_network=registry_match.get("verification_network"),
            confidence=0.95,
            explanation="El dominio coincide con el registro interno de fuentes.",
        )

    communication_type, confidence, explanation = _classify_non_radar(domain)
    return SourceClassification(
        is_radar_media=False,
        communication_type=communication_type,
        source_name=None,
        matched_domain=None,
        confidence=confidence,
        explanation=explanation,
    )


@lru_cache
def _load_radar_media() -> list[dict[str, str]]:
    if not RADAR_FILE.exists():
        return []
    with RADAR_FILE.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    items = payload.get("media", []) if isinstance(payload, dict) else payload
    return [
        {
            "name": item.get("name", "").strip(),
            "domain": _normalize_domain(item.get("domain", "")),
            "category": item.get("category"),
            "editorial_alignment": item.get("editorial_alignment"),
            "platform": item.get("platform"),
            "verification_network": item.get("verification_network"),
        }
        for item in items
        if item.get("domain")
    ]


def _match_radar_media(domain: str) -> dict[str, str] | None:
    for item in _load_radar_media():
        radar_domain = item["domain"]
        if domain == radar_domain or domain.endswith(f".{radar_domain}"):
            return item
    return None


@lru_cache
def _load_source_registry() -> list[dict[str, str]]:
    if not SOURCE_REGISTRY_FILE.exists():
        return []
    with SOURCE_REGISTRY_FILE.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    items = payload.get("sources", []) if isinstance(payload, dict) else payload
    return [
        {
            "name": item.get("name", "").strip(),
            "domain": _normalize_domain(item.get("domain", "")),
            "handle": _normalize_handle(item.get("handle")) or None,
            "communication_type": item.get("communication_type", "medio_no_radar"),
            "publisher_type": item.get("publisher_type", "medio_comunicacion"),
            "verification_network": item.get("verification_network"),
            "category": item.get("category"),
            "editorial_alignment": item.get("editorial_alignment"),
            "platform": item.get("platform"),
        }
        for item in items
        if (item.get("domain") or item.get("handle")) and item.get("active", True)
    ]


def _match_source_registry(domain: str, handle: str | None = None) -> dict[str, str] | None:
    for item in _load_source_registry():
        source_domain = item["domain"]
        source_handle = item.get("handle")
        if handle and source_handle and handle == source_handle:
            return item
        if _domain_matches(domain, SOCIAL_DOMAINS):
            continue
        if source_domain and (domain == source_domain or domain.endswith(f".{source_domain}")):
            return item
    return None


def find_registered_source(source_domain: str = "", handle: str | None = None) -> dict[str, str] | None:
    return _match_source_registry(_normalize_domain(source_domain), _normalize_handle(handle) or None)


def list_registered_sources_for_search(limit: int | None = None) -> list[dict[str, str]]:
    priority = {
        "medio_verificacion": 0,
        "medio_comunicacion_sitio_web": 1,
        "medio_nativo_digital": 2,
        "medio_digital_alineado_gobierno": 3,
        "democratizacion_informacion": 4,
    }
    sources = sorted(
        _load_source_registry(),
        key=lambda item: (
            priority.get(item.get("category") or "", 9),
            item.get("name") or "",
        ),
    )
    if limit is not None:
        return sources[:limit]
    return sources


def _classify_non_radar(domain: str) -> tuple[str, float, str]:
    if _domain_matches(domain, SOCIAL_DOMAINS):
        return "red_social", 0.95, "El dominio pertenece a una red social."
    if _domain_matches(domain, VIDEO_DOMAINS):
        return "plataforma_video", 0.95, "El dominio pertenece a una plataforma de video."
    if any(hint in domain for hint in GOV_HINTS):
        return "gobierno", 0.85, "El dominio tiene patron gubernamental."
    if any(hint in domain for hint in BLOG_HINTS):
        return "blog", 0.8, "El dominio tiene patron de blog o publicacion personal."
    if any(hint in domain for hint in NEWS_HINTS):
        return "medio_no_radar", 0.75, "Parece medio de comunicacion, pero no esta en la lista Radar."
    if any(hint in domain for hint in ORG_HINTS):
        return "institucion", 0.65, "El dominio parece institucional u organizacional."
    if domain:
        return "otro", 0.45, "No coincide con Radar ni con patrones conocidos de comunicacion."
    return "desconocido", 0.0, "No se pudo determinar el dominio de la fuente."


def _domain_matches(domain: str, candidates: set[str]) -> bool:
    return any(domain == candidate or domain.endswith(f".{candidate}") for candidate in candidates)


def _normalize_domain(domain: str) -> str:
    clean = domain.lower().strip()
    if "://" in clean:
        clean = urlparse(clean).netloc
    clean = clean.split("@")[-1].split(":")[0]
    return clean.removeprefix("www.")


def _extract_handle(url: str) -> str | None:
    parsed = urlparse(url)
    domain = _normalize_domain(parsed.netloc)
    if not _domain_matches(domain, SOCIAL_DOMAINS):
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if not parts:
        return None
    if parts[0] in {"p", "reel", "tv", "stories", "watch"} and len(parts) > 1:
        return _normalize_handle(parts[1])
    return _normalize_handle(parts[0])


def _normalize_handle(handle: str | None) -> str:
    if not handle:
        return ""
    return handle.lower().strip().lstrip("@")
