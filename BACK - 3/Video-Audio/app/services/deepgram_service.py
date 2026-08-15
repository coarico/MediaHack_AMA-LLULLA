"""
Speech-to-Text de respaldo / doble verificacion usando Deepgram

Este servicio es independiente del TranscriptionService principal (Whisper/Groq,
mantenido por el equipo) para no generar conflictos de merge con ese archivo.
Se usa desde perform_content_analysis() en main.py en dos escenarios:

    1. Backup: si la transcripcion principal falla o queda vacia, se usa
       Deepgram como alternativa para no perder la transcripcion.
    2. Doble verificacion: si la transcripcion principal funciona, se corre
       Deepgram en paralelo y se adjunta como transcription['deepgram_backup']
       para comparar ambos resultados.

Si DEEPGRAM_API_KEY no esta configurada (por ejemplo en el entorno de otro
dev que no la tenga en su .env), _get_client() lanza ValueError y quien lo
llama debe capturarla y continuar sin backup, sin afectar el flujo principal.
"""
import os
from typing import Dict
from app.config import settings


class DeepgramTranscriptionService:
    """Servicio de transcripcion de respaldo/verificacion usando Deepgram"""

    def __init__(self):
        self._client = None
        self.model = settings.deepgram_model
        self.language = settings.deepgram_language

    def _get_client(self):
        if self._client is None:
            if not settings.deepgram_api_key:
                raise ValueError(
                    "DEEPGRAM_API_KEY no esta configurada. "
                    "Definila en el archivo .env (ver .env.example) para "
                    "habilitar la transcripcion de respaldo con Deepgram."
                )
            from deepgram import AsyncDeepgramClient
            self._client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)
        return self._client

    async def transcribe(self, audio_path: str) -> Dict:
        """Transcribe un archivo de audio usando Deepgram"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        client = self._get_client()

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        print(f"🎙️ [Deepgram backup] Transcribing (model={self.model}, language={self.language})")

        response = await client.listen.v1.media.transcribe_file(
            request=audio_bytes,
            model=self.model,
            language=self.language,
            smart_format=True,
            punctuate=True,
            utterances=True,
            paragraphs=True,
        )

        alternative = response.results.channels[0].alternatives[0]
        text = (alternative.transcript or "").strip()

        segments = [
            {
                "text": (utt.transcript or "").strip(),
                "start": utt.start or 0.0,
                "end": utt.end or 0.0,
            }
            for utt in (response.results.utterances or [])
            if (utt.transcript or "").strip()
        ]

        duration = getattr(response.metadata, "duration", None) or 0.0

        print(f"✅ [Deepgram backup] Transcription complete: {len(text)} chars, {len(segments)} segments")

        return {
            "text": text,
            "language": self.language,
            "segments": segments,
            "duration": duration,
        }

    async def transcribe_video(self, video_path: str) -> Dict:
        """Extrae el audio del video (ffmpeg) y lo transcribe con Deepgram"""
        video_path_str = str(video_path)
        audio_path = video_path_str.replace(os.path.splitext(video_path_str)[1], '_deepgram_audio.wav')

        try:
            import imageio_ffmpeg
            import subprocess
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

            result = subprocess.run(
                [ffmpeg_exe, '-i', video_path_str, '-vn',
                 '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000',
                 '-y', audio_path],
                capture_output=True, text=True
            )

            if result.returncode != 0:
                raise Exception(f"ffmpeg failed: {result.stderr[:200]}")

            if not os.path.exists(audio_path):
                raise Exception(f"Audio file not created: {audio_path}")

            return await self.transcribe(audio_path)

        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)
