"""
routes/chat.py
--------------
POST /api/chat  — main pipeline endpoint
"""

import logging

from flask import Blueprint, request, jsonify

from services.pipeline_service import run_chat_pipeline

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    Request body (JSON):
        { "query": "show me sales orders for customer C001" }

    Response (JSON):
        {
          "success": bool,
          "message": str,
          "cds_view": str,
          "llm1_reasoning": str,
          "odata_url": str,
          "row_count": int,
          "visualization": {
            "type": "table|bar_chart|line_chart|pie_chart|none",
            "title": str,
            "columns": list | null,
            "rows": list | null,
            "x_axis": str | null,
            "y_axis": str | null,
            "label_field": str | null,
            "value_field": str | null
          },
          "error": str | null,
          "error_type": str | null
        }
    """
    body = request.get_json(silent=True)

    if not body or "query" not in body:
        return jsonify({
            "success": False,
            "message": "Request body must contain a 'query' field.",
            "error": "Missing 'query' field in request body.",
            "error_type": "BAD_REQUEST",
        }), 400

    raw_query = body["query"]

    if not isinstance(raw_query, str):
        return jsonify({
            "success": False,
            "message": "The 'query' field must be a string.",
            "error": "'query' must be a string.",
            "error_type": "BAD_REQUEST",
        }), 400

    logger.info("Chat request received. Query length: %d chars", len(raw_query))

    response_dict, status_code = run_chat_pipeline(raw_query)
    return jsonify(response_dict), status_code
