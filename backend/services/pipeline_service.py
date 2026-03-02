"""
services/pipeline_service.py
-----------------------------
Orchestrates the full chat pipeline end-to-end.

Steps:
  1. Validate & sanitise input
  2. Semantic search → top-K CDS view candidates
  3. LLM Call #1 → select best view + extract OData params
  4. Build safe OData URL
  5. Fetch SAP data via OData
  6. LLM Call #2 → summarise data + produce visualisation spec
  7. Assemble and return the final response dict
"""

import logging
from typing import Any, Optional

import config
from utils.validation import run_all_validations, QueryValidationError
from utils.odata_builder import build_odata_url, ODataBuildError
from services import search_service, llm_service, odata_service
from services.odata_service import ODataFetchError

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Response assembly helpers
# ─────────────────────────────────────────────

def _empty_visualization() -> dict:
    return {
        "type": "none",
        "title": "",
        "columns": None,
        "rows": None,
        "x_axis": None,
        "y_axis": None,
        "label_field": None,
        "value_field": None,
    }


def _success_response(
    message: str,
    cds_view: str,
    llm1_reasoning: str,
    odata_url: str,
    row_count: int,
    visualization: dict,
) -> dict:
    return {
        "success": True,
        "message": message,
        "cds_view": cds_view,
        "llm1_reasoning": llm1_reasoning,
        "odata_url": odata_url,
        "row_count": row_count,
        "visualization": visualization,
        "error": None,
        "error_type": None,
    }


def _error_response(
    message: str,
    error_code: str,
    cds_view: str = "",
    odata_url: str = "",
    row_count: int = 0,
) -> dict:
    return {
        "success": False,
        "message": message,
        "cds_view": cds_view,
        "llm1_reasoning": "",
        "odata_url": odata_url,
        "row_count": row_count,
        "visualization": _empty_visualization(),
        "error": message,
        "error_type": error_code,
    }


# ─────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────

def run_chat_pipeline(raw_query: str) -> tuple[dict, int]:
    """
    Execute the full pipeline for a single user query.

    Args:
        raw_query: The unprocessed user query string.

    Returns:
        (response_dict, http_status_code)

    The response_dict always contains:
        success, message, cds_view, llm1_reasoning,
        odata_url, row_count, visualization, error, error_type
    """

    # ── Step 1: Validate & sanitise ─────────────────────────────────────────
    try:
        safe_query = run_all_validations(raw_query, max_length=config.MAX_QUERY_LENGTH)
    except QueryValidationError as exc:
        logger.warning("Validation failed [%s]: %s", exc.error_type, exc)
        # Validation failures are user errors → 400
        return _error_response(str(exc), exc.error_type), 400

    # ── Step 2: Semantic search ──────────────────────────────────────────────
    try:
        candidates = search_service.search(safe_query, top_k=config.TOP_K_SEARCH)
    except Exception as exc:
        logger.exception("Search service failed: %s", exc)
        return _error_response("Search service unavailable.", "SEARCH_ERROR"), 500

    if not candidates:
        return (
            _error_response(
                "No relevant CDS views found for your query. Please try different search terms.",
                "NO_RESULTS",
            ),
            200,
        )

    # ── Step 3: LLM Call #1 — view selection + OData params ─────────────────
    try:
        selection = llm_service.call_llm_view_selection(safe_query, candidates)
    except Exception as exc:
        logger.exception("LLM #1 failed unexpectedly: %s", exc)
        # Fallback: use top-1 candidate
        selection = {
            "selected_view": candidates[0].get("name", ""),
            "reasoning": "LLM unavailable — defaulted to top semantic search result.",
            "odata_params": {"$top": "50"},
        }

    selected_view_name = selection.get("selected_view", "")
    llm1_reasoning     = selection.get("reasoning", "")
    odata_params       = selection.get("odata_params", {"$top": "50"})

    # Find the matching candidate to get its field whitelist
    matching_candidate = next(
        (c for c in candidates if c.get("name") == selected_view_name),
        candidates[0],  # fallback to top result if LLM returned an unknown name
    )
    known_fields = matching_candidate.get("field_names", [])

    logger.info("LLM #1 selected view: %s", selected_view_name)

    # ── Step 4: Build safe OData URL ─────────────────────────────────────────
    try:
        odata_url = build_odata_url(selected_view_name, odata_params, known_fields)
    except ODataBuildError as exc:
        logger.error("OData URL build failed: %s", exc)
        # Build a minimal fallback URL with no params
        try:
            odata_url = build_odata_url(selected_view_name, {"$top": "50"}, [])
        except ODataBuildError:
            return (
                _error_response(
                    f"Could not build a valid OData URL for view '{selected_view_name}'.",
                    "ODATA_BUILD_ERROR",
                    cds_view=selected_view_name,
                ),
                200,
            )

    logger.info("OData URL: %s", odata_url)

    # ── Step 5: Fetch SAP data ───────────────────────────────────────────────
    data_rows: list[dict] = []
    row_count: int = 0
    sap_error_message: Optional[str] = None

    try:
        data_rows, row_count = odata_service.fetch_odata(odata_url)
    except ODataFetchError as exc:
        logger.warning("OData fetch failed [%s]: %s", exc.error_code, exc)
        sap_error_message = str(exc)
        # Do not return early — LLM #2 can still provide a useful answer
        # from the CDS view metadata even without live data

    # ── Step 6: LLM Call #2 — summarise + visualisation spec ────────────────
    try:
        summary = llm_service.call_llm_summarize(
            safe_query,
            selected_view_name,
            odata_url,
            data_rows,
        )
    except Exception as exc:
        logger.exception("LLM #2 failed unexpectedly: %s", exc)
        summary = {
            "message": (
                sap_error_message
                or f"Retrieved {row_count} records from {selected_view_name}."
            ),
            "visualization": _empty_visualization(),
        }

    # If SAP fetch failed, prepend a warning to the LLM message
    message = summary.get("message", "")
    if sap_error_message and not data_rows:
        message = (
            f"⚠️ Live data could not be fetched: {sap_error_message}\n\n"
            + message
        )

    visualization = summary.get("visualization", _empty_visualization())

    # Ensure visualization always has all expected keys
    viz_defaults = _empty_visualization()
    viz_defaults.update(visualization)
    visualization = viz_defaults

    # ── Step 7: Assemble final response ──────────────────────────────────────
    return (
        _success_response(
            message=message,
            cds_view=selected_view_name,
            llm1_reasoning=llm1_reasoning,
            odata_url=odata_url,
            row_count=row_count,
            visualization=visualization,
        ),
        200,
    )
