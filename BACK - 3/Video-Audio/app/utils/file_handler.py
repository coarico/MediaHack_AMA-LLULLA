import os
import shutil
import uuid
import httpx
from pathlib import Path
from fastapi import UploadFile
from typing import Optional

from app.config import settings


class FileHandler:
    """Handle file operations for uploads and temporary storage"""
    
    def __init__(self):
        self.temp_dir = Path(settings.temp_dir)
        self.upload_dir = Path(settings.upload_dir)
        
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
    def validate_audio_file(self, file: UploadFile) -> None:
        """
        Validate audio file format and size
        
        Args:
            file: Uploaded file
            
        Raises:
            ValueError: If file is invalid
        """
        # Check file size
        if file.size and file.size > settings.max_file_size:
            raise ValueError(
                f"File size exceeds maximum allowed size of {settings.max_file_size / 1024 / 1024}MB"
            )
        
        # Check file extension
        if file.filename:
            extension = file.filename.split('.')[-1].lower()
            if extension not in settings.allowed_audio_formats:
                raise ValueError(
                    f"Invalid audio format. Allowed formats: {', '.join(settings.allowed_audio_formats)}"
                )
    
    def validate_video_file(self, file: UploadFile) -> None:
        """
        Validate video file format and size (for Programador 2)
        
        Args:
            file: Uploaded file
            
        Raises:
            ValueError: If file is invalid
        """
        if file.size and file.size > settings.max_file_size:
            raise ValueError(
                f"File size exceeds maximum allowed size of {settings.max_file_size / 1024 / 1024}MB"
            )
        
        if file.filename:
            extension = file.filename.split('.')[-1].lower()
            if extension not in settings.allowed_video_formats:
                raise ValueError(
                    f"Invalid video format. Allowed formats: {', '.join(settings.allowed_video_formats)}"
                )
    
    async def save_temp_file(self, file: UploadFile) -> Path:
        """
        Save uploaded file to temporary directory
        
        Args:
            file: Uploaded file
            
        Returns:
            Path to saved file
        """
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if file.filename else 'tmp'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = self.temp_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return file_path
    
    async def download_from_url(self, url: str) -> tuple[Path, dict]:
        """
        Download file from URL to temporary directory
        Supports YouTube and direct URLs
        
        Args:
            url: URL of the file
            
        Returns:
            Tuple of (Path to downloaded file, metadata dict or None)
            
        Raises:
            Exception: If download fails
        """
        # Check if it's a YouTube URL
        if 'youtube.com' in url or 'youtu.be' in url:
            return await self._download_youtube(url)
        
        # Regular URL download
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True, timeout=30.0)
            response.raise_for_status()
            
            # Determine file extension from URL or content-type
            file_extension = self._get_extension_from_url(url)
            if not file_extension:
                content_type = response.headers.get('content-type', '')
                file_extension = self._get_extension_from_content_type(content_type)
            
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = self.temp_dir / unique_filename
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(response.content)
            
            return file_path, None
    
    async def _download_youtube(self, url: str) -> tuple[Path, dict]:
        """
        Download video from YouTube using yt-dlp and extract metadata
        
        Args:
            url: YouTube URL
            
        Returns:
            Tuple of (Path to downloaded video file, metadata dict)
        """
        import yt_dlp
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        output_template = str(self.temp_dir / f"{unique_id}.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best[height<=720]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Extract metadata
            metadata = {
                'source_url': url,
                'title': info.get('title', ''),
                'channel': info.get('channel', ''),
                'channel_id': info.get('channel_id', ''),
                'uploader': info.get('uploader', ''),
                'upload_date': info.get('upload_date', ''),
                'description': info.get('description', ''),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'duration': info.get('duration', 0),
                'is_verified': info.get('channel_is_verified', False),
                'platform': 'YouTube'
            }
            
        return Path(filename), metadata
    
    def is_audio_file(self, file_path: Path) -> bool:
        """Check if file is an audio file based on extension"""
        extension = file_path.suffix[1:].lower()  # Remove the dot
        return extension in settings.allowed_audio_formats
    
    def is_video_file(self, file_path: Path) -> bool:
        """Check if file is a video file based on extension"""
        extension = file_path.suffix[1:].lower()
        return extension in settings.allowed_video_formats
    
    def cleanup_file(self, file_path: Path) -> None:
        """
        Delete a file
        
        Args:
            file_path: Path to file to delete
        """
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Warning: Could not delete file {file_path}: {e}")
    
    def cleanup_temp_directory(self) -> None:
        """Clean up all files in temporary directory"""
        try:
            if self.temp_dir.exists():
                for file_path in self.temp_dir.glob('*'):
                    if file_path.is_file():
                        file_path.unlink()
        except Exception as e:
            print(f"Warning: Could not clean temp directory: {e}")
    
    def _get_extension_from_url(self, url: str) -> Optional[str]:
        """Extract file extension from URL"""
        path = url.split('?')[0]  # Remove query parameters
        parts = path.split('.')
        if len(parts) > 1:
            extension = parts[-1].lower()
            all_formats = settings.allowed_audio_formats + settings.allowed_video_formats
            if extension in all_formats:
                return extension
        return None
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from content-type header"""
        content_type_map = {
            'audio/mpeg': 'mp3',
            'audio/wav': 'wav',
            'audio/ogg': 'ogg',
            'audio/mp4': 'm4a',
            'audio/flac': 'flac',
            'video/mp4': 'mp4',
            'video/x-msvideo': 'avi',
            'video/quicktime': 'mov',
            'video/x-matroska': 'mkv',
            'video/webm': 'webm'
        }
        return content_type_map.get(content_type, 'tmp')
