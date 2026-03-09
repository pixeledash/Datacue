"""
utils/odata_builder.py
----------------------
Safely constructs an OData URL from the parameters produced by LLM Call #1.
This is a critical security boundary: it whitelists allowed params, validates
field names against known metadata, and sanitises filter strings before
anything reaches the SAP system.
"""

import re
from urllib.parse import urlencode, quote, quote_plus
from typing import Optional

import config


# Only these OData system query options are allowed through
_ALLOWED_PARAMS = {"$filter", "$select", "$orderby", "$top", "$skip"}

# Characters that must never appear inside a $filter value
_FILTER_DANGEROUS = re.compile(r"[;\|`\\]|--|\bDROP\b|\bDELETE\b|\bEXEC\b", re.IGNORECASE)


class ODataBuildError(Exception):
    """Raised when the URL cannot be built safely."""


def _clean_view_name(raw_name: str) -> str:
    """
    Strip suffixes like ' (Basic)', ' (Composite)', ' (Consumption)' that
    appear in the metadata display names but not in the actual OData entity set.

    Example: 'I_SalesOrder (Basic)' → 'I_SalesOrder'
    """
    return re.sub(r"\s*\(.*?\)\s*$", "", raw_name).strip()


def _validate_field_names(field_str: str, known_fields: list[str]) -> str:
    """
    Given a comma-separated $select string, drop any field that does not
    appear in known_fields (case-insensitive).  Returns the cleaned string,
    or an empty string if nothing survives.
    """
    if not known_fields:
        return field_str  # no whitelist available — pass through as-is

    known_lower = {f.lower() for f in known_fields}
    requested = [f.strip() for f in field_str.split(",") if f.strip()]
    valid = [f for f in requested if f.lower() in known_lower]
    return ",".join(valid)


def _sanitize_filter(filter_str: str) -> str:
    """
    Basic sanitisation of $filter values produced by the LLM.
    Rejects the entire filter if dangerous patterns are found.
    """
    if _FILTER_DANGEROUS.search(filter_str):
        raise ODataBuildError(
            f"Unsafe pattern detected in $filter: '{filter_str}'"
        )
    return filter_str.strip()


def build_odata_url(
    view_name: str,
    odata_params: dict,
    known_fields: Optional[list[str]] = None,
) -> str:
    """
    Build a safe, fully-encoded OData URL.

    Args:
        view_name:    CDS view name (may contain ' (Basic)' suffix).
        odata_params: Raw params dict from LLM #1, e.g.
                      {"$filter": "...", "$top": "50", "$select": "..."}
        known_fields: List of valid field names for the selected view.
                      Used to whitelist $select entries.

    Returns:
        Full OData URL string with $format=json appended.

    Raises:
        ODataBuildError if the URL cannot be built safely.
    """
    clean_name = _clean_view_name(view_name)
    if not clean_name:
        raise ODataBuildError(f"Cannot derive a clean view name from '{view_name}'")

    base = (
        f"{config.SAP_BASE_URL}"
        f"{config.SAP_ODATA_PATH}"
        f"/{config.SAP_SERVICE}"
        f"/{clean_name}"
    )

    safe_params: dict[str, str] = {}

    for key, value in (odata_params or {}).items():
        key = key.strip()

        # Reject any param not on the whitelist
        if key not in _ALLOWED_PARAMS:
            continue

        # Drop None / "None" / "null" values — LLM sometimes returns these
        if value is None or str(value).strip().lower() in ("none", "null", ""):
            continue

        value = str(value).strip()

        if key == "$filter":
            value = _sanitize_filter(value)

        elif key == "$select":
            value = _validate_field_names(value, known_fields or [])
            if not value:
                continue  # all fields were invalid — skip $select entirely

        elif key == "$top":
            try:
                top_val = int(value)
                # Clamp to safe ceiling
                top_val = min(top_val, config.MAX_ODATA_TOP)
                value = str(top_val)
            except ValueError:
                value = "50"  # sensible default if LLM returned garbage

        elif key == "$skip":
            try:
                int(value)  # must be numeric
            except ValueError:
                continue

        safe_params[key] = value

    # Always include JSON format — must not be overridable
    safe_params["$format"] = "json"

    # Build query string manually to keep OData $ prefixes unencoded.
    # urlencode(quote_via=quote) would turn $filter → %24filter which SAP rejects.
    # Only the *values* should be percent-encoded, not the param keys.
    parts = []
    for k, v in safe_params.items():
        # Encode the value (spaces → %20, quotes → %27, etc.) but leave key as-is
        encoded_value = quote(str(v), safe="*-._~ ()'")
        parts.append(f"{k}={encoded_value}")

    # sap-client must always be present — it tells SAP which tenant to use.
    # It is NOT an OData system query option so it goes outside safe_params.
    if config.SAP_CLIENT:
        parts.append(f"sap-client={config.SAP_CLIENT}")

    query_string = "&".join(parts)

    return f"{base}?{query_string}"
