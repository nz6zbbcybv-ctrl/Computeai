#!/usr/bin/env python3
"""
Entry point for running the Flask application.
"""
from app.app import create_app
from app.config import Config

if __name__ == "__main__":
    app = create_app()
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )

