"""
services/search_service.py
--------------------------
Semantic search over the FAISS index using the sentence-transformer model.
Ported from app_e5_large.py — no Streamlit dependency.

The model and index are loaded once at module import and reused for every
request (equivalent to @st.cache_resource).
"""

import gc
import json
import pickle
import logging
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

import config

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Module-level singletons (loaded once)
# ─────────────────────────────────────────────
_model: Optional[SentenceTransformer] = None
_index: Optional[faiss.Index] = None
_meta: Optional[list] = None


def _load_model() -> SentenceTransformer:
    model = SentenceTransformer(config.EMBEDDING_MODEL)

    if config.EMBEDDING_USE_FP16 and torch.cuda.is_available():
        model = model.half()

    if config.EMBEDDING_KEEP_ON_CPU:
        model = model.to("cpu")
    else:
        model = model.to("cuda" if torch.cuda.is_available() else "cpu")

    logger.info("Sentence transformer loaded: %s", config.EMBEDDING_MODEL)
    return model


def _load_index() -> faiss.Index:
    if not Path(config.INDEX_FILE).exists():
        raise FileNotFoundError(f"FAISS index not found: {config.INDEX_FILE}")
    index = faiss.read_index(config.INDEX_FILE)
    logger.info("FAISS index loaded: %s (%d vectors)", config.INDEX_FILE, index.ntotal)
    return index


def _load_meta() -> list:
    if not Path(config.META_FILE).exists():
        raise FileNotFoundError(f"Metadata file not found: {config.META_FILE}")
    with open(config.META_FILE, "rb") as f:
        meta = pickle.load(f)
    logger.info("Metadata loaded: %d entries", len(meta))
    return meta


def _clear_gpu_cache() -> None:
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    gc.collect()


def initialise() -> None:
    """
    Explicitly load all resources. Call this once at Flask app startup
    so the first request is not slow.
    """
    global _model, _index, _meta
    _model = _load_model()
    _index = _load_index()
    _meta  = _load_meta()


def _ensure_loaded() -> None:
    """Lazy-load if initialise() was not called."""
    global _model, _index, _meta
    if _model is None:
        _model = _load_model()
    if _index is None:
        _index = _load_index()
    if _meta is None:
        _meta = _load_meta()


# ─────────────────────────────────────────────
# Public helpers
# ─────────────────────────────────────────────

def get_meta_count() -> int:
    _ensure_loaded()
    return len(_meta)


def _extract_details(raw_json: dict) -> dict:
    """
    Normalise the raw JSON stored in the metadata pickle.
    Returns a consistent dict regardless of whether the entry has a
    'details' sub-key or flat structure.
    """
    if not isinstance(raw_json, dict):
        return {"description": "", "fields": [], "capabilities": []}

    source = raw_json.get("details", raw_json)

    raw_fields = source.get("fields", [])

    # Fields may be stored as a plain string (older corpus) or a list of dicts
    if isinstance(raw_fields, str):
        # Convert "Field1, Field2, ..." into minimal dicts for consistency
        parsed_fields = [
            {"Field Name": f.strip(), "Description": "", "Data Type": ""}
            for f in raw_fields.split(",")
            if f.strip()
        ]
    elif isinstance(raw_fields, list):
        parsed_fields = raw_fields
    else:
        parsed_fields = []

    return {
        "description": source.get("description", ""),
        "fields": parsed_fields,                         # list of dicts
        "field_names": [f.get("Field Name", "") for f in parsed_fields],  # plain list for whitelist
        "capabilities": source.get("supportedCapabilities", [])
                        or source.get("supported_capabilities", {}).get("capabilities", []),
    }


# ─────────────────────────────────────────────
# Main search function
# ─────────────────────────────────────────────

def search(query: str, top_k: int = None) -> list[dict]:
    """
    Semantic search over the FAISS index.

    Args:
        query:  Sanitised user query.
        top_k:  Number of results to return (defaults to config.TOP_K_SEARCH).

    Returns:
        List of result dicts, each containing:
            name, display_name, score,
            description, fields (list of dicts), field_names (list of str),
            capabilities (list of str), raw_json (dict)
    """
    _ensure_loaded()

    if top_k is None:
        top_k = config.TOP_K_SEARCH

    # E5 models require a 'query: ' prefix; others do not
    formatted = f"query: {query}" if config.EMBEDDING_REQUIRES_PREFIX else query

    original_device = next(_model.parameters()).device

    try:
        if original_device.type == "cpu" and torch.cuda.is_available():
            _model.to("cuda")
            _clear_gpu_cache()

        q_emb = _model.encode(
            [formatted],
            batch_size=1,
            convert_to_numpy=True,
            show_progress_bar=False,
            device="cuda" if torch.cuda.is_available() else "cpu",
        ).astype("float32")

        faiss.normalize_L2(q_emb)
        D, I = _index.search(q_emb, top_k)

    finally:
        if original_device.type == "cpu" and torch.cuda.is_available():
            _model.to("cpu")
            _clear_gpu_cache()

    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0 or idx >= len(_meta):
            continue

        item = _meta[idx].copy()
        item["score"] = float(score)

        raw_json = json.loads(item.get("raw", "{}"))
        item["raw_json"] = raw_json

        details = _extract_details(raw_json)
        item["description"]  = details["description"]
        item["fields"]       = details["fields"]
        item["field_names"]  = details["field_names"]
        item["capabilities"] = details["capabilities"]

        results.append(item)

    return results
