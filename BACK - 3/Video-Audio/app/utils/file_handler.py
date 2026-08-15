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
        # Platforms supported by yt-dlp
        yt_dlp_platforms = [
            'youtube.com', 'youtu.be',
            'instagram.com', 'instagr.am',
            'tiktok.com',
            'facebook.com', 'fb.watch', 'fb.com',
            'twitter.com', 'x.com',
            'vimeo.com',
            'dailymotion.com', 'dai.ly',
            'twitch.tv',
            'reddit.com', 'redd.it',
            'pinterest.com', 'pin.it',
            'linkedin.com',
            'bilibili.com', 'b23.tv',
        ]
        
        if any(platform in url for platform in yt_dlp_platforms):
            return await self._download_with_ytdlp(url)
        
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
    
    async def _download_with_ytdlp(self, url: str) -> tuple[Path, dict]:
        """
        Download video from any supported platform using yt-dlp and extract metadata
        
        Supports: YouTube, Instagram, TikTok, Facebook, Twitter/X, Vimeo, etc.
        
        Args:
            url: URL of the video
            
        Returns:
            Tuple of (Path to downloaded video file, metadata dict)
        """
        import yt_dlp
        import imageio_ffmpeg
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        output_template = str(self.temp_dir / f"{unique_id}.%(ext)s")
        
        # Get ffmpeg binary from imageio-ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        
        ydl_opts = {
            'format': 'best[ext=mp4][height<=720]/best[height<=720]/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': ffmpeg_path,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.tiktok.com/',
            },
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Detect platform from extractor
                extractor = info.get('extractor_key', 'Unknown')
                
                # Extract metadata (works across platforms)
                metadata = {
                    'source_url': url,
                    'title': info.get('title', ''),
                    'channel': info.get('channel', '') or info.get('uploader', ''),
                    'channel_id': info.get('channel_id', ''),
                    'uploader': info.get('uploader', ''),
                    'upload_date': info.get('upload_date', ''),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'duration': info.get('duration', 0),
                    'is_verified': info.get('channel_is_verified', False),
                    'platform': extractor,
                    'thumbnail': info.get('thumbnail', ''),
                    'thumbnails': info.get('thumbnails', [])
                }
                
            return Path(filename), metadata
        except yt_dlp.utils.DownloadError as e:
            # Fallback: try alternative methods based on platform
            print(f"🔄 yt-dlp failed, trying alternative download methods...")
            try:
                result = await self._download_fallback(url)
                if result:
                    return result
            except Exception as fallback_err:
                print(f"⚠️ All fallback methods failed: {fallback_err}")
            raise ValueError(f"No se pudo descargar el video de esta plataforma. Intenta con YouTube u otra URL. ({str(e)[:80]})")
        except Exception as e:
            raise ValueError(f"Error al descargar: {str(e)[:100]}")
    
    async def _download_fallback(self, url: str) -> tuple[Path, dict]:
        """Fallback download for any platform when yt-dlp fails"""
        import httpx
        import imageio_ffmpeg
        
        # Detect platform
        is_tiktok = 'tiktok.com' in url
        platform = 'TikTok' if is_tiktok else 'Unknown'
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            download_url = None
            metadata = {
                'title': 'Video',
                'channel': '',
                'source_url': url,
                'platform': platform,
                'duration': 0.0,
                'view_count': 0,
                'upload_date': '',
                'is_verified': False,
            }
            
            if is_tiktok:
                # Use tikwm.com API for TikTok
                print("🔄 Trying tikwm.com for TikTok...")
                response = await client.get("https://www.tikwm.com/api/", params={'url': url})
                data = response.json()
                
                if data.get('code') != 0:
                    raise ValueError(f"tikwm: {data.get('msg', 'error')}")
                
                video_data = data.get('data', {})
                download_url = video_data.get('play') or video_data.get('wmplay')
                if not download_url:
                    raise ValueError("tikwm: no video URL")
                
                # Fix URL format
                if download_url.startswith('//'):
                    download_url = 'https:' + download_url
                elif not download_url.startswith('http'):
                    download_url = 'https://www.tikwm.com' + download_url
                
                metadata['title'] = video_data.get('title', 'TikTok Video')
                author = video_data.get('author')
                if isinstance(author, dict):
                    metadata['channel'] = author.get('nickname', '')
                metadata['duration'] = float(video_data.get('duration', 0))
                metadata['view_count'] = int(video_data.get('play_count', 0))
            else:
                # For other platforms, try direct download
                print("🔄 Trying direct HTTP download...")
                download_url = url
                metadata['title'] = url.split('/')[-1][:50]
            
            # Download the video file
            unique_id = str(uuid.uuid4())
            output_path = self.temp_dir / f"{unique_id}.mp4"
            
            video_response = await client.get(download_url)
            if video_response.status_code != 200:
                raise ValueError(f"Download failed: HTTP {video_response.status_code}")
            
            output_path.write_bytes(video_response.content)
            
            # Get duration with ffprobe
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            try:
                import subprocess
                import json as _json
                ffprobe_path = ffmpeg_path.replace('ffmpeg-win-x86_64', 'ffprobe-win-x86_64').replace('ffmpeg.exe', 'ffprobe.exe')
                probe = subprocess.run(
                    [ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', str(output_path)],
                    capture_output=True, text=True, timeout=10
                )
                if probe.returncode == 0:
                    fmt = _json.loads(probe.stdout).get('format', {})
                    metadata['duration'] = float(fmt.get('duration', 0))
            except:
                pass
            
            print(f"✅ Fallback download successful: {output_path.name}")
            return output_path, metadata
    
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
