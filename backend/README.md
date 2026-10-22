# Backend

Three Lambda functions, each an independent uv project (`src` package, Python 3.11+). Locally
each Lambda is served by a small FastAPI shim (`local_server.py`) that turns HTTP requests into
API Gateway events, so the handlers run unchanged.

```
┌──────────────────┐   documents    ┌──────────────────────┐   CSV    ┌─────────────────────┐
│  Scraper         │──────────────▶ │  Orchestrator        │◀──────── │  Trigger Upload     │
│  (data ingestion)│   + index      │  (retrieval + Claude)│          │  (client files)     │
└──────────────────┘                └──────────────────────┘          └─────────────────────┘
```

## Services

### [Scraper](./scraper-lambda/)
Collects documents from the public sources configured per industry in
`src/config/sources/<industry>.yaml` (strategies `single_url`, `crawl`, `live`). Every document
is saved with a `<file>.metadata.json` sidecar (industry, sections, year) used to filter
retrieval.

### [Orchestrator](./orchestrator-lambda/)
Generates the reports with Claude (Anthropic API):
- **Market Analysis** — retrieval per report section, then generation (crops, or any industry
  configured in the scraper YAML)
- **Market Position** — Claude reads the client's PDF together with the Market Analysis
- **Peer Analysis** — from the peer CSV, triggered when the CSV lands in `peer_data/`

Also builds the local vector index (`src/retrieval/indexer.py`) and serves the read API
(list reports, latest analysis per category, client report).

### [Trigger Upload](./trigger-upload-lambda/)
`POST /upload`: Excel files are converted to CSV (`peer_data/`), PDFs get an upload URL.

## Backends

| Variable | `local` (default) | AWS |
|---|---|---|
| `STORAGE_BACKEND` | `data/<bucket>/<key>` on disk | `s3` |
| `RETRIEVAL_BACKEND` | Chroma index in `.chroma/` + `BAAI/bge-m3` | `bedrock` (Knowledge Base) |

## Storage layout

```
data/
├── sra-thesis-raw-data/        # scraper output: raw/<industry>/<source>/...
├── sra-thesis-client-data/     # uploads: market_position_data/pdf/, peer_data/
└── sra-thesis-output/          # reports: market_analysis/, industry_analysis/<industry>/,
                                #          market_position/, peer_analysis/
```

## Running

See the root README (`scripts/dev.sh`, `scripts/demo.sh`). Per service:

```bash
cd orchestrator-lambda
uv sync --extra local-rag                              # local retrieval dependencies
uv run --extra local-rag python -m src.retrieval.indexer [--industry electricity] [--rebuild]
uv run --extra local-rag uvicorn local_server:app --port 8001
uv run --extra local-rag pytest

cd scraper-lambda
uv run python -m src.services.scraping.cli run --industry electricity --storage local --out ../../data/sra-thesis-raw-data

cd trigger-upload-lambda
uv run --group local uvicorn local_server:app --port 8002
```

`uv run` syncs the environment to exactly what the command asks for, so keep
`--extra local-rag` on every orchestrator command (otherwise the extra is uninstalled).
