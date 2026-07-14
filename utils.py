import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Union
import aiohttp
import aiofiles

logger = logging.getLogger(__name__)

class FileManager:
    """Handle file operations for the bridge."""
    
    def __init__(self, download_dir: str = 'downloads'):
        self.download_dir = Path(download_dir)
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Create download directory if it doesn't exist."""
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def get_temp_path(self, filename: str) -> Path:
        """Generate a temporary file path with timestamp."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        temp_filename = f"{name}_{timestamp}{ext}"
        return self.download_dir / temp_filename
    
    async def download_file(self, url: str, filename: str) -> Optional[Path]:
        """Download a file from URL to local storage."""
        try:
            temp_path = self.get_temp_path(filename)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        async with aiofiles.open(temp_path, 'wb') as f:
                            await f.write(await response.read())
                        logger.info(f"Downloaded file: {temp_path}")
                        return temp_path
                    else:
                        logger.error(f"Failed to download {url}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error downloading file {filename}: {e}")
            return None
    
    def delete_file(self, file_path: Union[str, Path]) -> bool:
        """Delete a temporary file."""
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted temp file: {path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def cleanup_directory(self):
        """Remove all files in the download directory."""
        try:
            for item in self.download_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            logger.info("Cleaned up download directory")
        except Exception as e:
            logger.error(f"Error cleaning directory: {e}")


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text for display purposes."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from filename."""
    unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def format_sender_name(username: Optional[str], display_name: Optional[str] = None) -> str:
    """Format sender name for display."""
    if display_name:
        return display_name
    return username or "Unknown User"


def is_bot_message(username: Optional[str] = None) -> bool:
    """Check if a message is from a bot."""
    if username and username.lower().endswith('bot'):
        return True
    return False
