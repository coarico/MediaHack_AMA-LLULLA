from app.schemas.news import ContentAttribution, CrossSourceCheck, SourceClassification, SourceVerification


def build_source_verification(
    source_classification: SourceClassification,
    content_attribution: ContentAttribution,
    cross_source_check: CrossSourceCheck,
) -> SourceVerification:
    reasons: list[str] = []
    verification_network = source_classification.verification_network

    if source_classification.is_radar_media:
        status = "radar_media"
        needs_validation = False
        recommendation = "Fuente en lista Radar. Validacion adicional opcional segun sensibilidad del contenido."
        reasons.append("El dominio coincide con la lista Radar configurada.")
    elif source_classification.registry_category == "medio_verificacion" or source_classification.editorial_alignment == "fact_checking":
        status = "ifcn_verified"
        needs_validation = False
        verification_network = source_classification.verification_network or "medio_verificacion"
        recommendation = "Fuente de verificacion registrada. Usar como evidencia de contraste, no como unica conclusion."
        reasons.append("La fuente esta registrada como medio de verificacion.")
    elif source_classification.source_name and source_classification.communication_type == "medio_no_radar":
        status = "registered_media"
        needs_validation = cross_source_check.related_coverage_count == 0
        recommendation = (
            "Fuente reconocida en el registro interno. Conviene contrastar si el tema es sensible o no hay cobertura relacionada."
        )
        reasons.append("El dominio coincide con el registro interno de fuentes.")
    elif content_attribution.platform_type == "red_social":
        status = "social_account"
        needs_validation = True
        recommendation = "Contenido publicado en red social. Se recomienda validar con noticias relacionadas o fuente primaria."
        reasons.append("La plataforma es red social; la cuenta puede compartir contenido de terceros.")
    elif source_classification.communication_type in {"medio_no_radar", "gobierno", "institucion"}:
        status = "unregistered_source"
        needs_validation = True
        recommendation = "Fuente no registrada. Se recomienda validar con fuentes relacionadas o documentos primarios."
        reasons.append("No se encontro coincidencia en Radar ni en el registro interno.")
    else:
        status = "unknown"
        needs_validation = True
        recommendation = "Fuente desconocida. Se recomienda validacion adicional antes de tomar decisiones."
        reasons.append("La fuente no pudo clasificarse con suficiente confianza.")

    if cross_source_check.related_coverage_count == 0:
        reasons.append("No hay noticias relacionadas disponibles para contrastar con la configuracion actual.")
    elif cross_source_check.independent_sources_count >= 2:
        reasons.append("Hay cobertura relacionada en multiples dominios.")

    return SourceVerification(
        status=status,
        source_name=source_classification.source_name or content_attribution.publisher_name,
        matched_domain=source_classification.matched_domain,
        verification_network=verification_network,
        needs_additional_validation=needs_validation,
        recommendation=recommendation,
        reasons=reasons,
    )
