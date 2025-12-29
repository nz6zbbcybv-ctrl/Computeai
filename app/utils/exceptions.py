"""
Custom exceptions for the application.
"""


class GroqAPIError(Exception):
    """Raised when Groq API returns an error."""
    pass


class SessionNotFoundError(Exception):
    """Raised when a session ID is not found."""
    pass


class InvalidRequestError(Exception):
    """Raised when a request is invalid."""
    pass


class LanguageDetectionError(Exception):
    """Raised when language detection fails."""
    pass


class TTSGenerationError(Exception):
    """Raised when TTS generation fails."""
    pass

