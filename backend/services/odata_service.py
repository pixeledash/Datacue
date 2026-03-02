"""
services/odata_service.py
-------------------------
Makes authenticated HTTP requests to the SAP OData service and normalises
the response into a plain list of dicts.

Handles:
  - OData v2 response shape  : { "d": { "results": [...] } }
  - OData v4 response shape  : { "value": [...] }
  - Auth errors (401/403)
  - SAP application errors (5xx)
  - Empty result sets (404 or empty results array)
  - Self-signed SSL certificates (verify=False)
"""

import logging
from typing import Optional

import requests
import urllib3
from requests.auth import HTTPBasicAuth

import config

# Suppress the InsecureRequestWarning that arises from verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Custom exception
# ─────────────────────────────────────────────

class ODataFetchError(Exception):
    """Raised when the SAP OData call fails in a way the caller should handle."""

    def __init__(self, message: str, error_code: str = "SAP_ERROR", status_code: int = 0):
        super().__init__(message)
        self.error_code  = error_code
        self.status_code = status_code


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _strip_metadata(row: dict) -> dict:
    """Remove the __metadata key that SAP OData v2 injects into every row."""
    return {k: v for k, v in row.items() if k != "__metadata"}


def _parse_response(data: dict) -> list[dict]:
    """
    Normalise OData v2 (d.results) and v4 (value) response shapes into a
    plain list of dicts.
    """
    # OData v2
    if "d" in data:
        inner = data["d"]
        if isinstance(inner, dict) and "results" in inner:
            rows = inner["results"]
        elif isinstance(inner, list):
            rows = inner
        else:
            rows = [inner]   # single-entity response
    # OData v4
    elif "value" in data:
        rows = data["value"]
    else:
        rows = []

    return [_strip_metadata(r) for r in rows if isinstance(r, dict)]


# ─────────────────────────────────────────────
# Public fetch function
# ─────────────────────────────────────────────

def fetch_odata(url: str) -> tuple[list[dict], int]:
    """
    Fetch data from the SAP OData endpoint.

    Args:
        url: Fully-formed OData URL (built by odata_builder).

    Returns:
        (rows, total_count) — rows is a list of dicts, total_count is len(rows).

    Raises:
        ODataFetchError for auth failures, permission errors, or SAP 5xx errors.
        Returns ([], 0) for 404 / empty result sets (not an exception — just no data).
    """
    if not config.SAP_USER or not config.SAP_PASSWORD:
        raise ODataFetchError(
            "SAP credentials not configured. Set SAP_USER and SAP_PASSWORD in .env",
            error_code="SAP_AUTH_ERROR",
        )

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    logger.info("OData fetch: %s", url)

    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(config.SAP_USER, config.SAP_PASSWORD),
            headers=headers,
            verify=config.SAP_VERIFY_SSL,
            timeout=config.SAP_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        raise ODataFetchError(
            f"SAP OData request timed out after {config.SAP_TIMEOUT}s",
            error_code="SAP_TIMEOUT",
        )
    except requests.exceptions.ConnectionError as exc:
        raise ODataFetchError(
            f"Cannot connect to SAP system: {exc}",
            error_code="SAP_CONNECTION_ERROR",
        )
    except requests.exceptions.RequestException as exc:
        raise ODataFetchError(
            f"SAP OData request failed: {exc}",
            error_code="SAP_ERROR",
        )

    # ── Handle HTTP error codes ──────────────────────────────────────────────
    if response.status_code == 401:
        raise ODataFetchError(
            "SAP authentication failed. Check SAP_USER and SAP_PASSWORD.",
            error_code="SAP_AUTH_ERROR",
            status_code=401,
        )

    if response.status_code == 403:
        raise ODataFetchError(
            "SAP returned 403 Forbidden. The user may lack authorisation for this CDS view.",
            error_code="SAP_FORBIDDEN",
            status_code=403,
        )

    if response.status_code == 404:
        # The entity set may not exist in the service — return empty, not error
        logger.warning("OData 404 for URL: %s", url)
        return [], 0

    if response.status_code >= 500:
        raise ODataFetchError(
            f"SAP system error (HTTP {response.status_code}). Check the SAP system logs.",
            error_code="SAP_ERROR",
            status_code=response.status_code,
        )

    if not response.ok:
        raise ODataFetchError(
            f"Unexpected HTTP {response.status_code} from SAP.",
            error_code="SAP_ERROR",
            status_code=response.status_code,
        )

    # ── Parse body ───────────────────────────────────────────────────────────
    try:
        data = response.json()
    except ValueError:
        raise ODataFetchError(
            "SAP returned a non-JSON response. The service may not support JSON format.",
            error_code="SAP_PARSE_ERROR",
        )

    rows = _parse_response(data)
    logger.info("OData fetch returned %d rows", len(rows))
    return rows, len(rows)


# ─────────────────────────────────────────────
# Health check helper
# ─────────────────────────────────────────────

def is_sap_reachable() -> bool:
    """
    Ping the SAP OData service root document to check reachability.
    Does not raise — returns True/False only.
    """
    if not config.SAP_USER or not config.SAP_PASSWORD:
        return False

    probe_url = (
        f"{config.SAP_BASE_URL}"
        f"{config.SAP_ODATA_PATH}"
        f"/{config.SAP_SERVICE}/"
    )
    try:
        resp = requests.get(
            probe_url,
            auth=HTTPBasicAuth(config.SAP_USER, config.SAP_PASSWORD),
            headers={"Accept": "application/json"},
            verify=config.SAP_VERIFY_SSL,
            timeout=5,
        )
        return resp.status_code in (200, 401)  # 401 means SAP is up, just credentials wrong
    except requests.exceptions.RequestException:
        return False
