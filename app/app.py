"""
Main Flask application.
"""
import atexit
from flask import Flask
from app.config import Config
from app.routes import health, chat, session
from app.services.session_manager import SessionManager
from app.utils.logger import setup_logger

logger = setup_logger("app")


def create_app() -> Flask:
    """
    Create and configure Flask application.
    
    Returns:
        Configured Flask app instance
    """
    app = Flask(
        __name__,
        static_folder=str(Config.STATIC_FOLDER),
        template_folder=str(Config.TEMPLATE_FOLDER)
    )
    
    # Register blueprints
    app.register_blueprint(health.health_bp)
    app.register_blueprint(chat.chat_bp)
    app.register_blueprint(session.session_bp)
    
    # Root route
    @app.route("/")
    def index():
        """Serve main page."""
        from flask import render_template
        return render_template("index.html")
    
    # Session cleanup on startup
    session_manager = SessionManager()
    session_manager.cleanup_expired_sessions()
    
    # Schedule periodic cleanup
    def schedule_cleanup():
        """Schedule session cleanup."""
        import threading
        import time
        
        def cleanup_loop():
            while True:
                time.sleep(Config.SESSION_CLEANUP_INTERVAL * 60)
                session_manager.cleanup_expired_sessions()
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        logger.info("Session cleanup scheduler started")
    
    schedule_cleanup()
    
    # Cleanup on exit
    atexit.register(lambda: session_manager.cleanup_expired_sessions())
    
    logger.info("Flask application initialized")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )

