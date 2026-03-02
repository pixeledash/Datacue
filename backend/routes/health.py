"""
routes/health.py
----------------
GET /api/health  — system health check endpoint
"""

import logging

from flask import Blueprint, jsonify

import config
from services import search_service, llm_service, odata_service

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    """
    Response (JSON):
        {
          "status": "ok" | "degraded",
          "faiss_index": "loaded",
          "meta_count": int,
          "ollama": "reachable" | "unreachable",
          "sap": "reachable" | "unreachable"
        }
    """
    # FAISS / metadata
    try:
        meta_count = search_service.get_meta_count()
        faiss_status = "loaded"
    except Exception as exc:
        logger.warning("Health check — search service error: %s", exc)
        meta_count = 0
        faiss_status = f"error: {exc}"

    # Ollama
    ollama_ok = llm_service.is_ollama_reachable()

    # SAP
    sap_ok = odata_service.is_sap_reachable()

    overall = "ok" if (faiss_status == "loaded" and ollama_ok) else "degraded"

    return jsonify({
        "status": overall,
        "faiss_index": faiss_status,
        "meta_count": meta_count,
        "ollama": "reachable" if ollama_ok else "unreachable",
        "sap": "reachable" if sap_ok else "unreachable",
        "embedding_model": config.EMBEDDING_MODEL,
        "llm_model": config.OLLAMA_MODEL,
    }), 200
