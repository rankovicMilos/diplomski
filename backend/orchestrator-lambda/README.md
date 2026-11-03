# Orchestrator Lambda

Report generation for sector credit risk analysis: retrieval over the scraped documents and
generation with Claude (Anthropic API).

## Structure

```
src/
├── handlers/
│   ├── orchestrator.py     # lambda_handler (routes by analysis_type), S3 trigger, API re-exports
│   └── api_handlers.py     # GET endpoints (list / latest per category / client report)
├── services/
│   ├── llm_service.py      # Claude calls (streaming, PDF input, server-side fallbacks)
│   ├── retrieval_service.py# retrieve_only -> local or bedrock backend
│   ├── storage.py          # storage functions -> local_storage or s3_service
│   └── industry_config.py  # report outline from the scraper's <industry>.yaml
├── retrieval/
│   ├── indexer.py          # builds the local index (extract text, chunk, embed)
│   ├── local.py            # Chroma + bge-m3 search
│   └── bedrock.py          # Bedrock Knowledge Base search
├── config/                 # settings.py (environment), prompts.py
└── utils/                  # query builders, JSON parsing, responses
local_server.py             # FastAPI shim: HTTP -> API Gateway event -> handler
```

Flow: event → retrieve (per section) → generate (Claude) → parse JSON → save → response.

## Analysis types

**Market analysis (crops):**
```json
{"analysis_type": "market_analysis", "crops": ["corn", "wheat"], "country": "Serbia"}
```

**Market analysis (any configured industry):** the sections come from the industry's source
YAML and retrieval is filtered to its documents. Saved to `industry_analysis/<industry>/`
(`"show_in_frontend": true` saves to `market_analysis/` instead).
```json
{"analysis_type": "market_analysis", "industry": "electricity"}
```

**Market position:** built only from the analyst's inputs (total revenue, revenue split per
commodity, currency and EUR/RSD rate) and a market analysis; no client documents are read.
Without `market_analysis_key`, the latest analysis of the client's industry (from `nace_code`)
is used.
```json
{
  "analysis_type": "market_position",
  "nace_code": "D35.14",
  "total_revenue": 1250000000,
  "commodities": [{"name": "hydro", "revenue_pct": 60}, {"name": "solar", "revenue_pct": 40}],
  "primary_currency": "RSD",
  "fx_rate_eur_rsd": 117.2,
  "fx_rate_date": "2025-12-31"
}
```

**Peer analysis:** triggered by a CSV in `peer_data/<analysis_id>.csv`, linked to
`market_position/<analysis_id>.json`; the sector name comes from that report's NACE code.

## Configuration

| Variable | Default | |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | required for generation |
| `CLAUDE_MODEL` | `claude-sonnet-5-5` | |
| `CLAUDE_EFFORT` / `CLAUDE_MAX_TOKENS` | `high` / `32000` | thinking depth, output budget |
| `STORAGE_BACKEND` | `local` | `s3` on AWS |
| `RETRIEVAL_BACKEND` | `local` | `bedrock` on AWS (needs `KNOWLEDGE_BASE_ID`) |
| `LOCAL_DATA_DIR` / `CHROMA_DIR` | `<repo>/data`, `<repo>/.chroma` | |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | must match between indexing and queries |
| `OUTPUT_BUCKET`, `CLIENT_DATA_BUCKET`, `RAW_DATA_BUCKET` | `sra-thesis-*` | |
| `SOURCES_CONFIG_S3_URI` / `SOURCES_CONFIG_DIR` | scraper's `src/config/sources` | industry YAMLs |

## Development

```bash
uv sync --extra local-rag
uv run --extra local-rag pytest
uv run --extra local-rag python -m src.retrieval.indexer --industry electricity
uv run --extra local-rag uvicorn local_server:app --port 8001     # http://localhost:8001/docs
```
