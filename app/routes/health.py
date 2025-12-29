"""
Health check endpoints.
"""
from flask import Blueprint, jsonify
from app.config import Config
from app.services.metrics import metrics_service
from app.utils.logger import setup_logger

logger = setup_logger("health")
health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON with health status
    """
    try:
        # Check if Groq API key is configured
        groq_configured = bool(Config.GROQ_API_KEY)
        
        # Get metrics
        stats = metrics_service.get_stats()
        
        health_status = {
            "status": "healthy" if groq_configured else "degraded",
            "groq_configured": groq_configured,
            "metrics": stats,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }
        
        status_code = 200 if groq_configured else 503
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

