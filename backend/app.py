"""
app.py
------
Flask application factory and entry point.

Usage:
    cd backend
    python app.py

Or with gunicorn for production:
    gunicorn -w 2 -b 0.0.0.0:5000 app:app
"""

import logging
import sys
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS

# Ensure the backend directory is on sys.path so all imports resolve correctly
sys.path.insert(0, str(Path(__file__).parent))

import config
from routes.chat import chat_bp
from routes.health import health_bp
from services import search_service

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Keep werkzeug and urllib3 at INFO to avoid flooding the console
logging.getLogger("werkzeug").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# App factory
# ─────────────────────────────────────────────

def create_app() -> Flask:
    app = Flask(__name__)

    # CORS — allow the Next.js frontend origin(s)
    CORS(app, resources={r"/api/*": {"origins": config.CORS_ORIGINS}})

    # Register route blueprints under /api prefix
    app.register_blueprint(chat_bp,   url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api")

    # ── Global error handlers ────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"success": False, "error": str(e), "error_type": "BAD_REQUEST"}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Endpoint not found.", "error_type": "NOT_FOUND"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "error": "Method not allowed.", "error_type": "METHOD_NOT_ALLOWED"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Unhandled 500 error: %s", e)
        return jsonify({"success": False, "error": "Internal server error.", "error_type": "INTERNAL_ERROR"}), 500

    return app


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    logger.info("Pre-loading FAISS index and embedding model…")
    try:
        search_service.initialise()
        logger.info("Resources loaded successfully.")
    except Exception as exc:
        logger.error("Failed to pre-load resources: %s", exc)
        logger.error("The server will still start but the first request will be slow.")

    logger.info("Starting Flask on http://0.0.0.0:5000")
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=config.FLASK_DEBUG,
        use_reloader=False,   # Disable reloader to prevent double model load
    )
