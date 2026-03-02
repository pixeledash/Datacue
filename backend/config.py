import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the backend directory
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ─────────────────────────────────────────────
# Paths (relative to project root, one level up)
# ─────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent

INDEX_FILE = str(PROJECT_ROOT / "cds_index.faiss")
META_FILE  = str(PROJECT_ROOT / "cds_meta.pkl")

# ─────────────────────────────────────────────
# Embedding model
# ─────────────────────────────────────────────
EMBEDDING_MODEL            = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_REQUIRES_PREFIX  = False   # E5 models need True; MiniLM does not
EMBEDDING_USE_FP16         = True
EMBEDDING_KEEP_ON_CPU      = True    # keep CPU so GPU is free for Ollama

TOP_K_SEARCH = 5

# ─────────────────────────────────────────────
# SAP OData
# ─────────────────────────────────────────────
SAP_BASE_URL   = os.getenv("SAP_BASE_URL", "https://bpts4hana01.bpterp.com:44300")
SAP_ODATA_PATH = "/sap/opu/odata/sap"
SAP_SERVICE    = os.getenv("SAP_SERVICE", "ZSB_CDS_API")
SAP_USER       = os.getenv("SAP_USER")
SAP_PASSWORD   = os.getenv("SAP_PASSWORD")
SAP_VERIFY_SSL = False   # SAP sandbox uses self-signed certs
SAP_TIMEOUT    = 15      # seconds

# ─────────────────────────────────────────────
# Ollama LLM
# ─────────────────────────────────────────────
OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_TIMEOUT = 120  # LLM calls can be slow

# ─────────────────────────────────────────────
# Security / validation limits
# ─────────────────────────────────────────────
MAX_QUERY_LENGTH     = 500
MAX_OUTPUT_LENGTH    = 5000
MAX_DATA_ROWS_TO_LLM = 30    # cap rows sent to LLM #2 to avoid token overflow
MAX_ODATA_TOP        = 200   # hard ceiling for $top in OData URLs

# ─────────────────────────────────────────────
# Flask / CORS
# ─────────────────────────────────────────────
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
FLASK_DEBUG  = os.getenv("FLASK_DEBUG", "0") == "1"
