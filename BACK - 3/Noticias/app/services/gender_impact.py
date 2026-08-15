import re
import unicodedata

from app.schemas.news import ExtractedArticle, GenderImpactAssessment, GenderImpactSignal, NewsAnalysis


SIGNAL_LABELS = {
    "estereotipos_genero": "Estereotipos de genero",
    "descalificacion_genero": "Descalificacion por genero",
    "sexualizacion": "Sexualizacion",
    "roles_familiares": "Roles familiares",
    "lenguaje_degradante": "Lenguaje degradante",
    "amenazas_intimidacion": "Amenazas o intimidacion",
    "contenido_manipulado": "Contenido manipulado",
    "hostigamiento_reiterado": "Hostigamiento reiterado",
}

GENDER_TERMS = (
    "mujer",
    "mujeres",
    "hombre",
    "hombres",
    "femenino",
    "masculino",
    "genero",
    "candidata",
    "candidato",
    "asambleista",
    "alcaldesa",
    "alcalde",
    "presidenta",
    "presidente",
)

PATTERNS = {
    "estereotipos_genero": (
        "mujer tenia que ser",
        "hombre tenia que ser",
        "las mujeres son",
        "los hombres son",
        "por ser mujer",
        "por ser hombre",
        "demasiado emocional",
        "histerica",
        "mandona",
        "debil",
    ),
    "descalificacion_genero": (
        "no sirve por ser mujer",
        "no sirve por ser hombre",
        "incapaz por ser mujer",
        "incapaz por ser hombre",
        "calladita se ve mejor",
        "vuelva a la cocina",
    ),
    "sexualizacion": (
        "cuerpo",
        "escote",
        "desnuda",
        "desnudo",
        "sexy",
        "vida intima",
        "amante",
        "sexual",
        "acostarse",
    ),
    "roles_familiares": (
        "mala madre",
        "buen padre",
        "mala esposa",
        "buen esposo",
        "su marido",
        "su mujer",
        "sus hijos",
        "como madre",
        "como esposa",
        "familia primero",
    ),
    "lenguaje_degradante": (
        "zorra",
        "puta",
        "perra",
        "bruja",
        "machona",
        "maricon",
        "marica",
        "humillada",
    ),
    "amenazas_intimidacion": (
        "amenaza",
        "amenazar",
        "la vamos a callar",
        "lo vamos a callar",
        "matar",
        "golpear",
        "violar",
        "intimidar",
    ),
    "contenido_manipulado": (
        "deepfake",
        "montaje",
        "video falso",
        "audio falso",
        "imagen manipulada",
        "contenido manipulado",
        "inteligencia artificial",
    ),
}

HIGH_SEVERITY = {"sexualizacion", "lenguaje_degradante", "amenazas_intimidacion", "contenido_manipulado"}


def assess_gender_impact(article: ExtractedArticle, analysis: NewsAnalysis) -> GenderImpactAssessment:
    text = _normalize(" ".join([article.title or "", article.text or "", *analysis.main_claims]))
    signals: list[GenderImpactSignal] = []

    for signal_type, patterns in PATTERNS.items():
        evidence = _first_evidence(text, patterns)
        if not evidence:
            continue
        if signal_type in {"sexualizacion", "amenazas_intimidacion", "contenido_manipulado"} and not _has_gender_context(text):
            continue
        severity = "alta" if signal_type in HIGH_SEVERITY else "media"
        signals.append(
            GenderImpactSignal(
                signal_type=signal_type,
                label=SIGNAL_LABELS[signal_type],
                evidence=evidence,
                severity=severity,
            )
        )

    repeated = _detect_repeated_harassment(text)
    if repeated:
        signals.append(repeated)

    score = _score(signals)
    if score >= 65 or sum(1 for signal in signals if signal.severity == "alta") >= 2:
        return GenderImpactAssessment(
            status="alerta_impacto_genero",
            status_label="ALERTA DE IMPACTO DE GENERO",
            score=max(score, 70),
            signals=signals[:6],
            explanation=(
                "Se identificaron multiples senales asociadas a ataques o expresiones relacionadas con genero. "
                "Requiere revision especializada."
            ),
            requires_specialized_review=True,
        )
    if signals:
        return GenderImpactAssessment(
            status="senales_para_revision",
            status_label="SENALES PARA REVISION",
            score=max(score, 35),
            signals=signals[:6],
            explanation=(
                "Se identificaron expresiones o elementos que podrian tener componente de genero. "
                "Se recomienda revisar contexto y evidencia."
            ),
            requires_specialized_review=False,
        )
    return GenderImpactAssessment(
        status="sin_senales_relevantes",
        status_label="SIN SENALES RELEVANTES",
        score=0,
        signals=[],
        explanation="No se identificaron elementos suficientes para activar una alerta de impacto de genero.",
        requires_specialized_review=False,
    )


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.lower()).strip()


def _has_gender_context(text: str) -> bool:
    return any(term in text for term in GENDER_TERMS)


def _first_evidence(text: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        index = text.find(pattern)
        if index >= 0:
            start = max(0, index - 60)
            end = min(len(text), index + len(pattern) + 60)
            return text[start:end].strip()
    return None


def _detect_repeated_harassment(text: str) -> GenderImpactSignal | None:
    hostile_terms = PATTERNS["lenguaje_degradante"] + PATTERNS["descalificacion_genero"]
    occurrences = sum(text.count(term) for term in hostile_terms)
    if occurrences < 3 or not _has_gender_context(text):
        return None
    return GenderImpactSignal(
        signal_type="hostigamiento_reiterado",
        label=SIGNAL_LABELS["hostigamiento_reiterado"],
        evidence="Se detecto repeticion de expresiones degradantes o descalificadoras con contexto de genero.",
        severity="alta",
    )


def _score(signals: list[GenderImpactSignal]) -> int:
    total = 0
    for signal in signals:
        total += {"baja": 15, "media": 30, "alta": 45}[signal.severity]
    return min(total, 100)
