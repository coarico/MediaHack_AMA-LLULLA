from app.schemas.news import CrossSourceCheck, RelatedNewsItem, SourceClassification
from app.services.source_classifier import classify_source


def build_cross_source_check(related_news: list[RelatedNewsItem]) -> CrossSourceCheck:
    if not related_news:
        return CrossSourceCheck(
            related_coverage_count=0,
            radar_media_coverage_count=0,
            independent_sources_count=0,
            contradictions_found=False,
            coverage_status="no_related_coverage",
            notes=["No se encontraron noticias relacionadas o no hay proveedor de busqueda configurado."],
        )

    domains = {item.source for item in related_news if item.source}
    classifications: list[SourceClassification] = [
        classify_source(item.url, item.source) for item in related_news if item.url
    ]
    radar_count = sum(1 for item in classifications if item.is_radar_media)

    if len(domains) >= 2:
        status = "multiple_sources"
    else:
        status = "single_source"

    notes = [
        f"Se encontraron {len(related_news)} resultados relacionados.",
        f"Dominios independientes detectados: {len(domains)}.",
    ]
    if radar_count:
        notes.append(f"{radar_count} resultados coinciden con medios Radar.")

    return CrossSourceCheck(
        related_coverage_count=len(related_news),
        radar_media_coverage_count=radar_count,
        independent_sources_count=len(domains),
        contradictions_found=False,
        coverage_status=status,
        notes=notes,
    )
