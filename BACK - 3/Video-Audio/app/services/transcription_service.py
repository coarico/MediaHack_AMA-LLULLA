"""
Speech-to-Text service using OpenAI Whisper
"""
import os
from typing import Dict, Optional
from app.config import settings


class TranscriptionService:
    """Service for converting audio to text using Whisper"""
    
    def __init__(self):
        """Initialize Whisper model"""
        self.model = None
        self.model_name = settings.whisper_model
        self.language = settings.whisper_language
        
    def _load_model(self):
        """Lazy load Whisper model"""
        if self.model is None:
            print(f"🎤 Loading Whisper model: {self.model_name}")
            import whisper
            self.model = whisper.load_model(self.model_name)
            print(f"✅ Whisper model loaded")
    
    async def transcribe(self, audio_path: str) -> Dict:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict with transcription results
        """
        self._load_model()
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Transcribe with Whisper
        result = self.model.transcribe(
            str(audio_path),  # Convert Path to string
            language=self.language,
            task="transcribe",
            verbose=False
        )
        
        return {
            'text': result['text'].strip(),
            'language': result.get('language', self.language),
            'segments': result.get('segments', []),
            'duration': self._get_duration(result)
        }
    
    def _get_duration(self, result: Dict) -> float:
        """Extract duration from Whisper result"""
        segments = result.get('segments', [])
        if segments:
            return segments[-1].get('end', 0.0)
        return 0.0
    
    async def transcribe_video(self, video_path: str) -> Dict:
        """
        Extract audio from video and transcribe
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dict with transcription results
        """
        import ffmpeg
        
        # Convert Path to string if needed
        video_path_str = str(video_path)
        
        # Extract audio to temporary file
        audio_path = video_path_str.replace(os.path.splitext(video_path_str)[1], '_audio.wav')
        
        try:
            # Use imageio-ffmpeg binary directly (more reliable than ffmpeg-python)
            import imageio_ffmpeg
            import subprocess
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            result = subprocess.run([
                ffmpeg_exe, '-i', video_path_str, '-vn',
                '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000',
                '-y', audio_path
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg failed: {result.stderr[:200]}")
            
            # Transcribe extracted audio
            result = await self.transcribe(audio_path)
            
            return result
            
        finally:
            # Clean up temporary audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)
