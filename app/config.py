"""
Configuration management for the Flask application.
Loads settings from environment variables and config files.
"""
import os
import json
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    # Load from project root directory
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass
except Exception:
    # If loading fails, continue without .env
    pass


class Config:
    """Application configuration."""
    
    # Base directory
    BASE_DIR = Path(__file__).parent.parent
    
    # Groq API configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY environment variable is required. "
            "Set it before starting the application."
        )
    
    # Load config from JSON
    CONFIG_FILE = BASE_DIR / "config" / "default.json"
    with open(CONFIG_FILE, "r") as f:
        _config_data = json.load(f)
    
    # Groq settings
    GROQ_MODELS = _config_data["groq"]["models"]
    GROQ_DEFAULT_MODEL = _config_data["groq"]["default_model"]
    GROQ_TEMPERATURE = _config_data["groq"]["temperature"]
    GROQ_MAX_TOKENS = _config_data["groq"]["max_tokens"]
    GROQ_TOP_P = _config_data["groq"]["top_p"]
    
    # Server settings
    HOST = _config_data["server"]["host"]
    PORT = _config_data["server"]["port"]
    DEBUG = _config_data["server"]["debug"]
    
    # Session settings
    SESSION_TIMEOUT_MINUTES = _config_data["session"]["timeout_minutes"]
    SESSION_CLEANUP_INTERVAL = _config_data["session"]["cleanup_interval_minutes"]
    
    # TTS settings
    TTS_ENABLED = _config_data["tts"]["enabled"]
    TTS_VOICE_EN = _config_data["tts"]["voice_en"]
    TTS_VOICE_HI = _config_data["tts"]["voice_hi"]
    TTS_SAMPLE_RATE = _config_data["tts"]["sample_rate"]
    
    # Metrics settings
    METRICS_ENABLED = _config_data["metrics"]["enabled"]
    METRICS_RETENTION_HOURS = _config_data["metrics"]["retention_hours"]
    
    # Database
    DATABASE_PATH = BASE_DIR / "app" / "storage" / "sessions.sqlite"
    
    # Static and template paths
    STATIC_FOLDER = BASE_DIR / "static"
    TEMPLATE_FOLDER = BASE_DIR / "templates"

