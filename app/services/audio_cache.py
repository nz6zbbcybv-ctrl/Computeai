"""
Audio cache service for TTS responses.
"""
import hashlib
from typing import Optional, Dict
from pathlib import Path
from app.config import Config
from app.utils.logger import setup_logger

logger = setup_logger("audio_cache")


class AudioCacheService:
    """Service for caching TTS audio files."""
    
    def __init__(self):
        """Initialize audio cache."""
        self.cache_dir = Path(Config.STATIC_FOLDER) / "audio_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache: Dict[str, str] = {}  # hash -> filepath
        logger.info(f"Audio cache initialized at {self.cache_dir}")
    
    def _get_hash(self, text: str, language: str) -> str:
        """
        Generate hash for text and language combination.
        
        Args:
            text: Text content
            language: Language code
            
        Returns:
            MD5 hash string
        """
        content = f"{text}:{language}".encode("utf-8")
        return hashlib.md5(content).hexdigest()
    
    def get(self, text: str, language: str) -> Optional[Path]:
        """
        Get cached audio file if exists.
        
        Args:
            text: Text content
            language: Language code
            
        Returns:
            Path to audio file or None if not cached
        """
        cache_key = self._get_hash(text, language)
        
        if cache_key in self.cache:
            filepath = Path(self.cache[cache_key])
            if filepath.exists():
                return filepath
        
        return None
    
    def put(self, text: str, language: str, audio_data: bytes) -> Path:
        """
        Store audio in cache.
        
        Args:
            text: Text content
            language: Language code
            audio_data: Audio bytes
            
        Returns:
            Path to cached file
        """
        cache_key = self._get_hash(text, language)
        filepath = self.cache_dir / f"{cache_key}.wav"
        
        with open(filepath, "wb") as f:
            f.write(audio_data)
        
        self.cache[cache_key] = str(filepath)
        logger.debug(f"Cached audio: {cache_key}")
        
        return filepath
    
    def clear(self):
        """Clear all cached audio files."""
        for filepath in self.cache_dir.glob("*.wav"):
            filepath.unlink()
        
        self.cache.clear()
        logger.info("Audio cache cleared")

