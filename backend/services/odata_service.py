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
  - CSRF token fetch (required by some SAP OData services)
"""

import logging
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import requests
import urllib3
from requests.auth import HTTPBasicAuth

import config

# Suppress the InsecureRequestWarning that arises from verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# Module-level session — reuses TCP connections and SAP session cookies
# (sap-usercontext, MYSAPSSO2) across all requests in this Flask process.
_session: Optional[requests.Session] = None
_csrf_token: Optional[str] = None


def _log_request_hook(response, *args, **kwargs):
    """Hook: log every outgoing request's method, URL, and headers at DEBUG level."""
    req = response.request
    logger.debug("→ %s %s", req.method, req.url)
    logger.debug("→ Request headers: %s", dict(req.headers))
    logger.debug("← Response HTTP %d | headers: %s", response.status_code, dict(response.headers))


def _get_session() -> requests.Session:
    """
    Return a persistent requests.Session configured for SAP.

    Key differences from a plain requests.get():
    - No Content-Type header on GET (Content-Type on a GET confuses SAP ICM)
    - Browser-like User-Agent (SAP ICM can block 'python-requests/x.x')
    - Cookies are preserved across calls (MYSAPSSO2, sap-usercontext)
    - Debug hook logs every request + response header pair
    """
    global _session
    if _session is None:
        _session = requests.Session()
        _session.auth    = HTTPBasicAuth(config.SAP_USER, config.SAP_PASSWORD)
        _session.verify  = config.SAP_VERIFY_SSL

        # Fix 1: NO Content-Type on GET — sending it causes SAP ICM to
        #         reject the request and serve its HTML login page (401 HTML)
        # Fix 2: Browser-like User-Agent — SAP ICM can redirect/block
        #         requests whose UA looks like a script/bot
        _session.headers.update({
            "Accept":       "application/json",
            "User-Agent":   (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })

        # Pre-set the SAP client cookie so it takes precedence over
        # whatever sap-usercontext the 401 response tries to set.
        _session.cookies.set(
            "sap-usercontext",
            f"sap-client={config.SAP_CLIENT}",
            domain=config.SAP_BASE_URL.split("//")[-1].split(":")[0],
        )

        # Fix 4: attach debug-logging hook to every response
        _session.hooks["response"].append(_log_request_hook)

    return _session


def _fetch_csrf_token() -> Optional[str]:
    """
    Fix 3: Fetch the SAP CSRF token required by some OData services.

    SAP OData v2 services often require a valid x-csrf-token on every
    modifying request (POST/PUT/DELETE). Some systems also require it on
    GET if the ICM profile has csrf_prevention enabled for all verbs.

    Procedure:
      GET {service_root}  with header  x-csrf-token: Fetch
      SAP responds with   header       x-csrf-token: <token>
      All subsequent requests include  x-csrf-token: <token>

    Returns the token string, or None if the server does not provide one
    (in which case we simply don't attach it — no harm done).
    """
    global _csrf_token
    if _csrf_token:
        return _csrf_token

    service_root = (
        f"{config.SAP_BASE_URL}"
        f"{config.SAP_ODATA_PATH}"
        f"/{config.SAP_SERVICE}/"
    )
    try:
        session = _get_session()
        resp = session.get(
            service_root,
            headers={"x-csrf-token": "Fetch"},
            timeout=config.SAP_TIMEOUT,
        )
        token = resp.headers.get("x-csrf-token")
        if token and token.lower() != "required":
            _csrf_token = token
            logger.info("CSRF token acquired: %s", _csrf_token[:10] + "…")
        else:
            logger.debug("SAP did not return a CSRF token — proceeding without one")
    except requests.exceptions.RequestException as exc:
        logger.warning("CSRF token fetch failed (non-fatal): %s", exc)

    return _csrf_token


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

    session = _get_session()

    # Fix 3: attach CSRF token if SAP provides one
    request_headers = {}
    token = _fetch_csrf_token()
    if token:
        request_headers["x-csrf-token"] = token

    logger.info("OData fetch: %s", url)

    try:
        response = session.get(
            url,
            headers=request_headers,
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
    logger.info("SAP OData response: HTTP %d", response.status_code)

    if response.status_code == 401:
        body_preview = response.text[:300].replace("\n", " ")
        logger.error("SAP 401 body preview: %s", body_preview)
        # If www-authenticate: Basic is present, SAP accepted the auth scheme but
        # rejected the credentials ("Anmeldung fehlgeschlagen" = Login Failed).
        # If the header is absent, ICM is blocking before Basic Auth is evaluated.
        has_basic_challenge = "basic" in response.headers.get("www-authenticate", "").lower()
        if has_basic_challenge:
            detail = (
                "SAP credentials rejected (HTTP 401). "
                "Check SAP_USER and SAP_PASSWORD in your .env file."
            )
        else:
            detail = (
                "SAP ICM is serving its login page without a Basic Auth challenge — "
                "Basic Auth may be disabled at the ICM level, or the User-Agent is being blocked."
            )
        raise ODataFetchError(detail, error_code="SAP_AUTH_ERROR", status_code=401)

    if response.status_code == 403:
        raise ODataFetchError(
            "SAP returned 403 Forbidden. The user may lack authorisation for this CDS view.",
            error_code="SAP_FORBIDDEN",
            status_code=403,
        )

    if response.status_code == 404:
        # $select may contain CDS-view fields that the OData service doesn't expose
        # (corpus metadata ≠ fields actually published by ZSB_CDS_API). Strip $select
        # and retry once so SAP returns all fields it does expose.
        parsed = urlparse(url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        if "$select" in params:
            params.pop("$select")
            new_query = urlencode({k: v[0] for k, v in params.items()})
            retry_url = urlunparse(parsed._replace(query=new_query))
            logger.warning(
                "OData 404 with $select — retrying without $select: %s", retry_url
            )
            return fetch_odata(retry_url)
        logger.warning("OData 404 — entity set not found or no records: %s", url)
        return [], 0

    if response.status_code >= 500:
        raise ODataFetchError(
            f"SAP system error (HTTP {response.status_code}). Check the SAP system logs.",
            error_code="SAP_ERROR",
            status_code=response.status_code,
        )

    if not response.ok:
        # On HTTP 400 the LLM may have generated an invalid $filter (wrong type,
        # placeholder value, Python None literal, etc.). Strip $filter and retry
        # once before giving up — same pattern as the 404/$select retry above.
        if response.status_code == 400:
            parsed = urlparse(url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            if "$filter" in params:
                params.pop("$filter")
                new_query = urlencode({k: v[0] for k, v in params.items()})
                retry_url = urlunparse(parsed._replace(query=new_query))
                logger.warning(
                    "OData 400 with $filter — retrying without $filter: %s", retry_url
                )
                return fetch_odata(retry_url)
        logger.error("SAP unexpected status %d. Body: %s", response.status_code, response.text[:500])
        raise ODataFetchError(
            f"Unexpected HTTP {response.status_code} from SAP.",
            error_code="SAP_ERROR",
            status_code=response.status_code,
        )

    # ── Parse body ───────────────────────────────────────────────────────────
    try:
        data = response.json()
    except ValueError:
        logger.error("SAP non-JSON response body: %s", response.text[:300])
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
    Ping the SAP OData service root to check reachability.
    Does not raise — returns True/False only.
    Note: 401 counts as reachable (SAP is up, credentials may be wrong).
    """
    if not config.SAP_USER or not config.SAP_PASSWORD:
        return False

    probe_url = (
        f"{config.SAP_BASE_URL}"
        f"{config.SAP_ODATA_PATH}"
        f"/{config.SAP_SERVICE}/"
    )
    try:
        session = _get_session()
        resp = session.get(probe_url, timeout=5)
        return resp.status_code in (200, 401)
    except requests.exceptions.RequestException:
        return False


def reset_session() -> None:
    """
    Force-reset the module-level session and CSRF token.
    Useful if credentials change at runtime or after an auth failure.
    """
    global _session, _csrf_token
    _session = None
    _csrf_token = None
    logger.info("SAP session reset")
