"""
LLM analysis service using Groq (Llama 3.3 70B).
Analyzes video transcription with AI to provide intelligent verdicts.
Optimized for minimal token usage: single call, concise JSON output.
"""
import json
import httpx
from typing import Dict, Optional
from app.config import settings


class LLMAnalyzer:
    """Analyze transcription using Groq LLM"""

    def __init__(self):
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def _is_available(self) -> bool:
        return bool(self.api_key)

    async def check_relevance(self, title: str = '', channel: str = '', description: str = '') -> Dict:
        """
        Quick relevance check using only metadata (no transcription needed).
        Determines if content is suitable for fact-checking/verification.

        Returns:
            Dict with 'is_relevant' (bool), 'reason' (str), 'category' (str)
        """
        if not self._is_available():
            return {'is_relevant': True, 'reason': 'Sin API key, asumiendo relevante', 'category': 'desconocido'}

        system_prompt = (
            "Eres un clasificador de contenido. Determinas si un video/audio es relevante "
            "para verificación de información, fact-checking o análisis político/electoral. "
            "Respondes SOLO en JSON válido."
        )

        user_prompt = (
            f"Clasifica este contenido según su metadata:\n\n"
            f"Título: {title or 'No disponible'}\n"
            f"Canal: {channel or 'No disponible'}\n"
            f"Descripción: {(description or 'No disponible')[:500]}\n\n"
            f"¿Es relevante para verificación de información, fact-checking, política, "
            f"noticias, discurso público, o claims verificables?\n\n"
            f"NO es relevante si es: música, canciones, chistes, entretenimiento, gameplay, "
            f"tutoriales de cocina, vlogs personales, contenido deportivo sin claims, "
            f"comedia, covers, remixes, letras de canciones, etc.\n\n"
            f"Si el título parece ser el nombre de un archivo (ej: 'cancion.mp3', 'video.mp4'), "
            f"usa esa pista pero sé conservador: si no hay indicios claros de contenido político "
            f"o noticioso, marca como NO relevante.\n\n"
            f"Responde en JSON:\n"
            '{{\n'
            '  "is_relevant": true|false,\n'
            '  "category": "politica|noticias|discurso|entretenimiento|musica|deportes|otro",\n'
            '  "reason": "breve explicación de por qué es o no relevante (máx 150 chars)"\n'
            '}}'
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 200,
            "response_format": {"type": "json_object"},
        }

        try:
            print(f"🔍 Checking content relevance...")
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.api_url, headers=headers, json=payload
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                result = json.loads(content)
                print(f"{'✅' if result.get('is_relevant') else '⛔'} Relevance: {result.get('category', 'N/A')} - {result.get('reason', 'N/A')}")
                return result

        except Exception as e:
            print(f"⚠️ Relevance check failed: {e}, assuming relevant")
            return {'is_relevant': True, 'reason': 'Error en clasificación, asumiendo relevante', 'category': 'desconocido'}

    async def analyze_transcription(
        self,
        transcription: str,
        title: str = "",
        channel: str = "",
        web_articles: list = None,
    ) -> Optional[Dict]:
        """
        Analyze transcription with LLM. Single API call, concise output.

        Args:
            transcription: Full transcription text
            title: Video title
            channel: Channel name
            web_articles: Related web articles from WebSearcher

        Returns:
            Dict with LLM analysis or None if unavailable
        """
        if not self._is_available():
            print("⚠️ Groq API key not configured, skipping LLM analysis")
            return None

        # Use title as fallback if transcription is too short
        if not transcription or len(transcription.strip()) < 10:
            if title and len(title.strip()) >= 5:
                transcription = f"[Video sin transcripción clara. Título: {title}]"
                print(f"ℹ️ Using title as fallback for LLM analysis (transcription too short)")
            else:
                return None

        # Truncate transcription to save tokens (max ~2000 chars)
        trans_truncated = transcription[:2000]
        if len(transcription) > 2000:
            trans_truncated += "... [truncado]"

        # Build context from web articles (max 3, short)
        web_context = ""
        if web_articles:
            for i, article in enumerate(web_articles[:3]):
                web_context += f"\n- {article.get('title', '')} ({article.get('source', '')})"
                snippet = article.get('snippet', '')[:150]
                if snippet:
                    web_context += f": {snippet}"

        # Concise system prompt to minimize token usage
        system_prompt = (
            "Eres un analista de contenido electoral y político para Ecuador. "
            "Analizas transcripciones de videos y das un veredicto estructurado. "
            "También detectas si el contenido parece generado o manipulado por IA: "
            "voz sintética, guion robótico, narración generada artificialmente, "
            "escenarios ficticios presentados como reales, o animaciones IA. "
            "Respondes SOLO en formato JSON válido, sin texto adicional."
        )

        user_prompt = (
            f"Analiza esta transcripción de un video.\n\n"
            f"Título: {title or 'No disponible'}\n"
            f"Canal: {channel or 'No disponible'}\n"
        )
        if web_context:
            user_prompt += f"Noticias relacionadas encontradas:{web_context}\n"

        user_prompt += (
            f"\nTranscripción:\n{trans_truncated}\n\n"
            f"Evalúa los siguientes aspectos:\n"
            f"1. ¿El contenido es verídico, engañoso o falso?\n"
            f"2. ¿La transcripción parece generada por IA? (voz sintética, guion robótico, "
            f"narración artificial, escenario ficticio, animación IA, avatar digital)\n"
            f"3. ¿Hay indicios de manipulación o recortes engañosos?\n\n"
            f"Responde en JSON con esta estructura exacta:\n"
            '{{\n'
            '  "tema_principal": "breve descripción del tema (máx 100 chars)",\n'
            '  "veredicto": "AUTÉNTICO|MIXTO|ENGAÑOSO|FALSO",\n'
            '  "confianza": 0-100,\n'
            '  "resumen": "resumen de 2-3 oraciones sobre el contenido",\n'
            '  "afirmaciones_clave": ["afirmación 1", "afirmación 2", "afirmación 3"],\n'
            '  "contexto_politico": "contexto relevante (máx 200 chars)",\n'
            '  "coincide_con_fuentes": true|false,\n'
            '  "indicios_ia": "Descripción de indicios de generación por IA detectados, o \"No se detectaron indicios\" (máx 200 chars)",\n'
            '  "observaciones": "nota sobre manipulación, recortes, generación IA, o algo relevante (máx 200 chars)"\n'
            '}}'
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 800,
            "response_format": {"type": "json_object"},
        }

        try:
            print(f"🤖 Sending transcription to Groq ({self.model})...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url, headers=headers, json=payload
                )
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # Parse JSON response
                result = json.loads(content)

                # Add metadata
                result["model_used"] = self.model
                result["tokens_used"] = data.get("usage", {}).get("total_tokens", 0)

                print(f"✅ LLM analysis complete: {result.get('veredicto', 'N/A')} "
                      f"({result.get('confianza', 0)}% confianza, "
                      f"{result.get('tokens_used', 0)} tokens)")

                return result

        except httpx.HTTPStatusError as e:
            print(f"⚠️ Groq API error: {e.response.status_code} - {e.response.text[:200]}")
            return None
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse LLM JSON response: {e}")
            return None
        except Exception as e:
            print(f"⚠️ LLM analysis failed: {e}")
            return None
