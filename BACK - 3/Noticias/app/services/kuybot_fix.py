# Fix script - rewrite critical functions

NEW_SYSTEM_PROMPT = """Eres Kuybot, verificador de noticias de AMA LLU IA.

TAREA: Redacta un análisis CLARO sobre si una noticia es confiable.

PROHIBIDO:
- Frases repetidas ("no se encontró evidencia suficiente")
- Párrafos conceptuales sobre verificación
- Secciones de "Bibliografía"
- Explicaciones duplicadas

OBLIGATORIO:
- Análisis específico: qué encontraste, qué NO encontraste
- Diferencia clara: datos de otros años son CONTEXTO, no contradicción
- Párrafos cortos y directos
- Responde EN ESPAÑOL claro

ESTRUCTURA:
1. Resumen (1-2 líneas)
2. Análisis por claim (✓ Coincide / ✗ Contradice / ? No confirma)
3. Conclusión (máx 3 líneas)

URLs: [Leer más](URL)
"""

def _build_claim_summary_NEW(payload):
    """Estructura claims evaluados en texto claro."""
    claims = payload.get("claim_analysis") or []
    if not claims:
        return "No hay claims para analizar."

    lines = []
    status_emoji = {"confirmado": "✓", "contradicho": "✗", "no_confirmado": "?", "contexto_insuficiente": "?"}
    
    for i, claim in enumerate(claims[:5], 1):
        claim_text = claim.get("claim", "N/A")
        status_dict = claim.get("status", {})
        status_val = status_dict.get("status", "no_confirmado") if isinstance(status_dict, dict) else "no_confirmado"
        reasoning = status_dict.get("reasoning", "") if isinstance(status_dict, dict) else ""
        
        emoji = status_emoji.get(status_val, "?")
        lines.append(f"{emoji} [{status_val.upper()}] {claim_text}")
        if reasoning:
            lines.append(f"   → {reasoning}")
        lines.append("")
    
    return "\n".join(lines)


def _format_short_url_NEW(url):
    """Convierte URL larga en [Leer más](url)."""
    if not url:
        return ""
    return f"[Leer más]({url})"


EXPLICIT_INSTRUCTIONS_TEMPLATE = """
ANÁLISIS DE VERIFICACIÓN - DATOS ESTRUCTURADOS:

Pregunta del usuario: {question}
Noticia verificada: {news_title}

--- CLAIMS ANALIZADOS ---
{claims_text}

--- TU TAREA ---
1. Redacta resumen ejecutivo (1-2 líneas máximo)
2. Explica CADA claim diferente de forma específica (no repitas)
3. Conclusión final: ¿Es confiable esta información?
4. NO uses "Bibliografía"
5. URLs como: [Leer más](URL)
"""
