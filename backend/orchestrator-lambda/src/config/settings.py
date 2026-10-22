"""
Centralized configuration settings for the orchestrator lambda.

All environment variables and constants are defined here to provide
a single source of truth for configuration across the application.
"""
import os
from datetime import datetime, timezone
from pathlib import Path


# Backends: "local" runs everything on this machine, "s3"/"bedrock" use AWS
STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")
RETRIEVAL_BACKEND = os.environ.get("RETRIEVAL_BACKEND", "local")

# Local backends: buckets are folders under LOCAL_DATA_DIR, the vector index is in CHROMA_DIR
_REPO_ROOT = Path(__file__).resolve().parents[4]
LOCAL_DATA_DIR = Path(os.environ.get("LOCAL_DATA_DIR", _REPO_ROOT / "data"))
CHROMA_DIR = Path(os.environ.get("CHROMA_DIR", _REPO_ROOT / ".chroma"))
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")

# AWS (only used with the s3 / bedrock backends)
AWS_REGION = os.environ.get("AWS_REGION", "eu-central-1")
KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID")

# Buckets (folder names under LOCAL_DATA_DIR with the local backend)
OUTPUT_BUCKET = os.environ.get("OUTPUT_BUCKET", "sra-thesis-output")
CLIENT_DATA_BUCKET = os.environ.get("CLIENT_DATA_BUCKET", "sra-thesis-client-data")
MARKET_ANALYSIS_BUCKET = os.environ.get("MARKET_ANALYSIS_BUCKET", OUTPUT_BUCKET)
PEER_DATA_BUCKET = os.environ.get("PEER_DATA_BUCKET", CLIENT_DATA_BUCKET)
RAW_DATA_BUCKET = os.environ.get("RAW_DATA_BUCKET", "sra-thesis-raw-data")

# Scraper source configs (<industry>.yaml), used for industry market analyses.
# SOURCES_CONFIG_S3_URI (s3://bucket/prefix) wins; otherwise the scraper's folder is read.
SOURCES_CONFIG_S3_URI = os.environ.get("SOURCES_CONFIG_S3_URI")
SOURCES_CONFIG_DIR = Path(os.environ.get(
    "SOURCES_CONFIG_DIR",
    _REPO_ROOT / "backend" / "scraper-lambda" / "src" / "config" / "sources",
))

# CORS Configuration
CORS_ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://localhost:3000")

# Claude (Anthropic API) inference configuration. The key is read from ANTHROPIC_API_KEY.
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
CLAUDE_EFFORT = os.environ.get("CLAUDE_EFFORT", "high")
# Output budget incl. the model's thinking. Reports are ~10K tokens of JSON; the rest leaves
# room for thinking so the JSON is not cut off.
CLAUDE_MAX_TOKENS = int(os.environ.get("CLAUDE_MAX_TOKENS", 32000))

# Retrieval configuration
DEFAULT_RESULTS_PER_SECTION = 70  # For per-section retrieval mode

# Analysis period: the last N completed years (in 2026: [2024, 2025]). Same rule as the
# scraper's core/period.py, so reports cover exactly the data the scraper keeps.
ANALYSIS_YEARS_BACK = int(os.environ.get("ANALYSIS_YEARS_BACK", 2))
_CURRENT_YEAR = datetime.now(timezone.utc).year

# Default values
DEFAULT_COUNTRY = "Serbia"
DEFAULT_YEARS = list(range(_CURRENT_YEAR - ANALYSIS_YEARS_BACK, _CURRENT_YEAR))
DEFAULT_CROPS = ["corn", "wheat", "soybean", "sunflower"]
