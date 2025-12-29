"""
Session management endpoints.
"""
from flask import Blueprint, request, jsonify
from app.services.session_manager import SessionManager
from app.utils.logger import setup_logger
from app.utils.exceptions import SessionNotFoundError

logger = setup_logger("session")
session_bp = Blueprint("session", __name__)
session_manager = SessionManager()


@session_bp.route("/api/session", methods=["POST"])
def create_session():
    """
    Create a new chat session.
    
    Request body (optional):
        {
            "language": "en",
            "model": "llama3-8b"
        }
    
    Returns:
        JSON with session_id
    """
    try:
        data = request.get_json() or {}
        language = data.get("language")
        model = data.get("model")
        
        session_id = session_manager.create_session(
            language=language,
            model=model
        )
        
        return jsonify({
            "session_id": session_id,
            "status": "created"
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to create session",
            "message": str(e)
        }), 500


@session_bp.route("/api/session/<session_id>", methods=["GET"])
def get_session(session_id: str):
    """
    Get session information and messages.
    
    Args:
        session_id: Session ID
        
    Returns:
        JSON with session data and messages
    """
    try:
        session = session_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                "error": "Session not found"
            }), 404
        
        messages = session_manager.get_messages(session_id)
        
        return jsonify({
            "session": dict(session),
            "messages": messages
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get session: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to get session",
            "message": str(e)
        }), 500

