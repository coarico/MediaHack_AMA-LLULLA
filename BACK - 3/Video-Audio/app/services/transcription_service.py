"""
Speech-to-Text service using OpenAI Whisper
"""
import os
import asyncio
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
        
        # Ensure ffmpeg is available for Whisper (it looks for 'ffmpeg' in PATH)
        import imageio_ffmpeg
        import shutil
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        # Whisper looks for 'ffmpeg' executable name, but imageio-ffmpeg uses a different name
        # Copy/symlink it as 'ffmpeg.exe' in the same directory
        ffmpeg_renamed = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
        if not os.path.exists(ffmpeg_renamed):
            try:
                shutil.copy2(ffmpeg_exe, ffmpeg_renamed)
            except Exception:
                pass
        if ffmpeg_dir not in os.environ.get('PATH', ''):
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Transcribe with Whisper (run in thread to not block event loop)
        result = await asyncio.to_thread(
            self.model.transcribe,
            str(audio_path),
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
        # Convert Path to string if needed
        video_path_str = str(video_path)
        
        # Extract audio to temporary file
        audio_path = video_path_str.replace(os.path.splitext(video_path_str)[1], '_audio.wav')
        
        try:
            # Use imageio-ffmpeg binary directly
            import imageio_ffmpeg
            import subprocess
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            print(f"🎬 Extracting audio with: {ffmpeg_exe}")
            print(f"   Input: {video_path_str}")
            print(f"   Output: {audio_path}")
            
            result = subprocess.run(
                [ffmpeg_exe, '-i', video_path_str, '-vn',
                 '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000',
                 '-y', audio_path],
                capture_output=True, text=True
            )
            
            print(f"   ffmpeg return code: {result.returncode}")
            if result.returncode != 0:
                print(f"   ffmpeg stderr: {result.stderr[:300]}")
                raise Exception(f"ffmpeg failed: {result.stderr[:200]}")
            
            if not os.path.exists(audio_path):
                raise Exception(f"Audio file not created: {audio_path}")
            
            print(f"   Audio file size: {os.path.getsize(audio_path)} bytes")
            
            # Transcribe extracted audio
            result = await self.transcribe(audio_path)
            
            return result
            
        finally:
            # Clean up temporary audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)
