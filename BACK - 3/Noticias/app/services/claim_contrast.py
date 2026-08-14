from app.schemas.news import ClaimContrast, RelatedNewsItem, VerifiableClaim


OFFICIAL_HINTS = ("gob", "gov", "inec", "cne", "msp", "ministerio", "contratacion")


def build_claim_contrasts(
    claims: list[VerifiableClaim],
    related_news: list[RelatedNewsItem],
    max_items: int = 5,
) -> list[ClaimContrast]:
    contrasts: list[ClaimContrast] = []
    source_names = _source_names(related_news)
    official_sources = [name for name in source_names if _looks_official(name)]

    for index, claim in enumerate(claims[:max_items], start=1):
        status, label, explanation = _contrast_status(claim, related_news, official_sources)
        evidence = related_news[0].url if related_news else None
        contrasts.append(
            ClaimContrast(
                timestamp=None,
                claim=claim.claim,
                status=status,
                status_label=label,
                explanation=explanation,
                sources_consulted=(official_sources or source_names)[:5],
                evidence_url=evidence,
            )
        )

    if not contrasts:
        contrasts.append(
            ClaimContrast(
                timestamp=None,
                claim="No se detectaron afirmaciones verificables en el contenido analizado.",
                status="no_verificable",
                status_label="NO VERIFICABLE",
                explanation=(
                    "El contenido identificado corresponde a una descripcion general, opinion o texto sin datos "
                    "puntuales que puedan contrastarse automaticamente."
                ),
                sources_consulted=source_names[:5],
                evidence_url=related_news[0].url if related_news else None,
            )
        )

    return contrasts


def _contrast_status(
    claim: VerifiableClaim,
    related_news: list[RelatedNewsItem],
    official_sources: list[str],
) -> tuple[str, str, str]:
    if claim.type not in {"estadistica", "evento", "cita", "acusacion", "fecha", "lugar"}:
        return (
            "no_verificable",
            "NO VERIFICABLE",
            "La afirmacion parece opinion, interpretacion o contenido sin datos comprobables directos.",
        )

    if not related_news:
        return (
            "sin_respaldo_suficiente",
            "SIN RESPALDO SUFICIENTE",
            (
                "No se encontro evidencia publica suficiente para confirmar esta afirmacion en los terminos "
                "planteados. Esto no significa automaticamente que sea incorrecta."
            ),
        )

    if claim.type == "estadistica":
        if official_sources:
            return (
                "requiere_contexto",
                "REQUIERE CONTEXTO",
                (
                    "Existen fuentes oficiales o institucionales relacionadas, pero la afirmacion debe compararse "
                    "con el mismo periodo, alcance y metodologia."
                ),
            )
        return (
            "informacion_a_contrastar",
            "INFORMACION A CONTRASTAR",
            (
                "Hay cobertura relacionada, pero no se detecto una fuente oficial suficiente para confirmar la cifra "
                "o el alcance mencionado."
            ),
        )

    if official_sources:
        return (
            "requiere_contexto",
            "REQUIERE CONTEXTO",
            (
                "La afirmacion tiene fuentes publicas relacionadas. Para evaluarla correctamente se deben revisar "
                "fechas, alcance y documento original."
            ),
        )

    return (
        "informacion_a_contrastar",
        "INFORMACION A CONTRASTAR",
        "Se encontraron noticias relacionadas, pero conviene revisar la evidencia antes de sacar una conclusion.",
    )


def _source_names(related_news: list[RelatedNewsItem]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for item in related_news:
        name = item.source_name or item.source
        if not name:
            continue
        key = name.lower()
        if key not in seen:
            seen.add(key)
            names.append(name)
    return names


def _looks_official(name: str) -> bool:
    clean = name.lower()
    return any(hint in clean for hint in OFFICIAL_HINTS)
