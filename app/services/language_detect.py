"""
Language detection service for English, Hindi, and Hinglish.
"""
import re
from typing import Literal
from app.utils.logger import setup_logger
from app.utils.exceptions import LanguageDetectionError

logger = setup_logger("language_detect")

# Unicode ranges for Devanagari script
DEVANAGARI_RANGE = re.compile(r'[\u0900-\u097F]')


class LanguageDetectionService:
    """Service for detecting language in text."""
    
    def detect(self, text: str) -> Literal["en", "hi", "hinglish"]:
        """
        Detect language in text.
        
        Rules:
        - If contains Devanagari characters → Hindi or Hinglish
        - If Devanagari ratio > 0.3 → Hindi
        - If Devanagari ratio <= 0.3 → Hinglish
        - Otherwise → English
        
        Args:
            text: Input text to analyze
            
        Returns:
            Language code: 'en', 'hi', or 'hinglish'
            
        Raises:
            LanguageDetectionError: If detection fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for language detection, defaulting to English")
            return "en"
        
        try:
            # Find all Devanagari characters
            devanagari_chars = DEVANAGARI_RANGE.findall(text)
            devanagari_count = len(devanagari_chars)
            
            # Count total characters (excluding whitespace)
            total_chars = len(re.sub(r'\s+', '', text))
            
            if total_chars == 0:
                return "en"
            
            # Calculate ratio
            devanagari_ratio = devanagari_count / total_chars if total_chars > 0 else 0
            
            # Decision logic
            if devanagari_count == 0:
                # No Devanagari characters → English
                detected = "en"
            elif devanagari_ratio > 0.3:
                # High Devanagari ratio → Hindi
                detected = "hi"
            else:
                # Low Devanagari ratio → Hinglish (code-mixed)
                detected = "hinglish"
            
            logger.debug(
                f"Language detected: {detected} "
                f"(Devanagari: {devanagari_count}/{total_chars}, ratio: {devanagari_ratio:.2f})"
            )
            
            return detected
            
        except Exception as e:
            error_msg = f"Language detection failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LanguageDetectionError(error_msg) from e
    
    def get_system_prompt(self, language: Literal["en", "hi", "hinglish"]) -> str:
        """
        Get system prompt based on detected language.
        
        Args:
            language: Detected language code
            
        Returns:
            System prompt string
        """
        prompts = {
            "en": (
                "You are a helpful, knowledgeable AI assistant. "
                "Respond naturally and conversationally in English. "
                "Be concise, accurate, and friendly."
            ),
            "hi": (
                "आप एक सहायक, ज्ञानी AI सहायक हैं। "
                "हिंदी में स्वाभाविक और बातचीत के तरीके से जवाब दें। "
                "संक्षिप्त, सटीक और मित्रतापूर्ण रहें।"
            ),
            "hinglish": (
                "You are a helpful, knowledgeable AI assistant. "
                "Respond naturally in Hinglish (Hindi-English mix). "
                "Use a mix of Hindi and English as appropriate. "
                "Be concise, accurate, and friendly."
            )
        }
        
        return prompts.get(language, prompts["en"])

