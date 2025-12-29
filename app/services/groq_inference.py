"""
Groq API inference service with streaming support.
"""
import time
from typing import Iterator, Dict, Any, Optional
from groq import Groq

from app.config import Config
from app.utils.logger import setup_logger
from app.utils.exceptions import GroqAPIError

logger = setup_logger("groq_inference")


class GroqInferenceService:
    """Service for interacting with Groq API."""
    
    def __init__(self):
        """Initialize Groq client."""
        if not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required")
        
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.default_model = Config.GROQ_MODELS.get(
            Config.GROQ_DEFAULT_MODEL,
            "llama-3.1-8b-instant"
        )
        logger.info(f"Groq inference service initialized with model: {self.default_model}")
    
    def get_model_name(self, model_key: str) -> str:
        """
        Get actual Groq model name from config key.
        
        Args:
            model_key: Model key from config
            
        Returns:
            Actual Groq model name
        """
        return Config.GROQ_MODELS.get(model_key, self.default_model)
    
    def stream_completion(
        self,
        messages: list,
        model_key: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream completion from Groq API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model_key: Model key from config
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            
        Yields:
            Dict with 'type' and 'content' or 'state' and 'message'
            
        Raises:
            GroqAPIError: If API call fails
        """
        model = self.get_model_name(model_key or Config.GROQ_DEFAULT_MODEL)
        temperature = temperature if temperature is not None else Config.GROQ_TEMPERATURE
        max_tokens = max_tokens if max_tokens is not None else Config.GROQ_MAX_TOKENS
        top_p = top_p if top_p is not None else Config.GROQ_TOP_P
        
        start_time = time.time()
        
        try:
            # Send status update
            yield {
                "type": "status",
                "state": "thinking",
                "message": f"Groq model {model} inference started"
            }
            
            # Create streaming request
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=True
            )
            
            # Stream tokens
            full_response = ""
            token_count = 0
            
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        token = delta.content
                        full_response += token
                        token_count += 1
                        
                        yield {
                            "type": "token",
                            "content": token
                        }
            
            # Calculate metrics
            elapsed = time.time() - start_time
            tokens_per_sec = token_count / elapsed if elapsed > 0 else 0
            
            # Send completion status
            yield {
                "type": "status",
                "state": "complete",
                "message": f"Generated {token_count} tokens in {elapsed:.2f}s ({tokens_per_sec:.1f} tokens/s)",
                "metrics": {
                    "latency": elapsed,
                    "tokens": token_count,
                    "tokens_per_sec": tokens_per_sec,
                    "model": model
                }
            }
            
        except Exception as e:
            # Check if it's an API error
            error_msg = f"Groq API error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield {
                "type": "status",
                "state": "error",
                "message": error_msg
            }
            raise GroqAPIError(error_msg) from e
    
    def get_available_models(self) -> Dict[str, str]:
        """
        Get available models mapping.
        
        Returns:
            Dict mapping model keys to actual model names
        """
        return Config.GROQ_MODELS.copy()

