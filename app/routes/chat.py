"""
Chat endpoints with streaming support.
"""
import json
import time
from flask import Blueprint, request, Response, stream_with_context
from app.services.groq_inference import GroqInferenceService
from app.services.language_detect import LanguageDetectionService
from app.services.session_manager import SessionManager
from app.services.metrics import metrics_service
from app.utils.logger import setup_logger
from app.utils.exceptions import GroqAPIError, SessionNotFoundError, InvalidRequestError

logger = setup_logger("chat")
chat_bp = Blueprint("chat", __name__)

groq_service = GroqInferenceService()
language_service = LanguageDetectionService()
session_manager = SessionManager()


@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    """
    Chat endpoint with streaming SSE response.
    
    Request body:
        {
            "message": "Hello",
            "session_id": "uuid",
            "model": "llama3-8b" (optional),
            "temperature": 0.7 (optional),
            "max_tokens": 2048 (optional),
            "top_p": 0.9 (optional)
        }
    
    Returns:
        Server-Sent Events stream
    """
    try:
        data = request.get_json()
        
        if not data:
            raise InvalidRequestError("Request body is required")
        
        message = data.get("message")
        if not message or not message.strip():
            raise InvalidRequestError("Message is required")
        
        session_id = data.get("session_id")
        if not session_id:
            # Create new session
            session_id = session_manager.create_session()
            logger.info(f"Created new session for chat: {session_id}")
        
        # Verify session exists
        session = session_manager.get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # Detect language
        detected_language = language_service.detect(message)
        system_prompt = language_service.get_system_prompt(detected_language)
        
        # Get conversation history
        history = session_manager.get_conversation_history(session_id)
        
        # Build messages for Groq API
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})
        
        # Save user message
        session_manager.add_message(session_id, "user", message)
        
        # Get model and parameters
        model_key = data.get("model")
        temperature = data.get("temperature")
        max_tokens = data.get("max_tokens")
        top_p = data.get("top_p")
        
        # Stream response
        def generate():
            start_time = time.time()
            full_response = ""
            token_count = 0
            success = True
            
            try:
                for event in groq_service.stream_completion(
                    messages=messages,
                    model_key=model_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p
                ):
                    # Send event as SSE
                    yield f"data: {json.dumps(event)}\n\n"
                    
                    # Track metrics
                    if event.get("type") == "token":
                        full_response += event.get("content", "")
                        token_count += 1
                    elif event.get("type") == "status" and event.get("state") == "complete":
                        metrics = event.get("metrics", {})
                        latency = metrics.get("latency", time.time() - start_time)
                        tokens_per_sec = metrics.get("tokens_per_sec", 0)
                        model = metrics.get("model", "unknown")
                        
                        # Record metrics
                        metrics_service.record_request(
                            latency=latency,
                            tokens=token_count,
                            tokens_per_sec=tokens_per_sec,
                            model=model,
                            success=True
                        )
                
                # Save assistant response
                if full_response:
                    session_manager.add_message(session_id, "assistant", full_response)
                
            except GroqAPIError as e:
                success = False
                error_event = {
                    "type": "status",
                    "state": "error",
                    "message": f"Groq API error: {str(e)}"
                }
                yield f"data: {json.dumps(error_event)}\n\n"
                
                # Record error metrics
                elapsed = time.time() - start_time
                metrics_service.record_request(
                    latency=elapsed,
                    tokens=0,
                    tokens_per_sec=0,
                    model="unknown",
                    success=False
                )
                
            except Exception as e:
                success = False
                logger.error(f"Unexpected error in chat stream: {str(e)}", exc_info=True)
                error_event = {
                    "type": "status",
                    "state": "error",
                    "message": f"Internal error: {str(e)}"
                }
                yield f"data: {json.dumps(error_event)}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
        
    except InvalidRequestError as e:
        logger.warning(f"Invalid request: {str(e)}")
        return jsonify({
            "error": "Invalid request",
            "message": str(e)
        }), 400
        
    except SessionNotFoundError as e:
        logger.warning(f"Session not found: {str(e)}")
        return jsonify({
            "error": "Session not found",
            "message": str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@chat_bp.route("/api/models", methods=["GET"])
def get_models():
    """
    Get available Groq models.
    
    Returns:
        JSON with available models
    """
    try:
        models = groq_service.get_available_models()
        return jsonify({
            "models": models,
            "default": groq_service.default_model
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get models: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to get models",
            "message": str(e)
        }), 500

