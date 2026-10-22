# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

"Sector Risk Analysis", a bachelor thesis project built on an enterprise POC. Scrapers collect public Serbian/EU market data per industry. A local vector index (Chroma + `BAAI/bge-m3`) makes it searchable, and an orchestrator calls **Claude via the Anthropic API** to write JSON reports (Market Analysis, Market Position, Peer Analysis). A Next.js app shows the reports. Domain terms are defined in `CONTEXT.md`, which is a glossary only. "Client" there means the company being assessed, never the lender.

The project runs **fully locally**. The components are still AWS Lambda handlers. Locally, a FastAPI shim per Lambda (`local_server.py`) turns HTTP requests into API Gateway proxy events and calls the unchanged handlers. `infrastructure/` (Terraform) describes the original AWS deployment and is reference only; it is not used to run the project.

The repo has three independent toolchains: `frontend/` (Next.js), `backend/<lambda>/` (separate uv projects, each with a top-level `src` package, so they cannot be imported into one process) and `infrastructure/`. The `*/github/workflows/` folders hold the original per-repo CI and are inactive.

## Commands

```bash
cp .env.example .env            # needs ANTHROPIC_API_KEY
scripts/dev.sh                  # orchestrator :8001, upload :8002, frontend :3000
scripts/demo.sh electricity     # scrape -> index -> market analysis (needs dev.sh running)
scripts/demo.sh cereals [--skip-scrape]
```

Orchestrator (`backend/orchestrator-lambda`). **Always pass `--extra local-rag`**: `uv run` syncs the environment exactly, so omitting it uninstalls chromadb, torch and the rest.
```bash
uv run --extra local-rag pytest
uv run --extra local-rag pytest tests/test_indexer.py::test_headings_start_new_chunks
uv run --extra local-rag python -m src.retrieval.indexer [--industry X] [--rebuild]
uv run --extra local-rag uvicorn local_server:app --port 8001
```

Scraper (`backend/scraper-lambda`), with ruff configured:
```bash
uv run python -m src.services.scraping.cli validate
uv run python -m src.services.scraping.cli list --industry electricity --status all
uv run python -m src.services.scraping.cli run --industry cereals --storage local --out ../../data/sra-thesis-raw-data
uv run ruff check src/
```

Trigger-upload (`backend/trigger-upload-lambda`): `uv run --group local uvicorn local_server:app --port 8002`.

Frontend (`frontend/`): `npm run dev`, `npm run build` (static export to `out/`), `npm run lint`. There is no test runner.

Infrastructure: `cd infrastructure/environment/poc && terraform init -backend=false && terraform validate`.

## Architecture

### Backend switches (`.env`)
- `STORAGE_BACKEND=local|s3`. Local mode stores buckets as folders: `data/<bucket>/<key>`.
  - Orchestrator: `services/storage.py` re-exports either `local_storage.py` or `s3_service.py`, which have the same 7 functions.
  - Trigger-upload: `LocalStorageService` subclasses `S3Service`. Its "presigned" PDF URL points at `PUT /local-upload/<key>` on the upload server.
- `RETRIEVAL_BACKEND=local|bedrock`. `services/retrieval_service.retrieve_only` lazily imports `src/retrieval/local.py` (Chroma) or `src/retrieval/bedrock.py` (Knowledge Base). Both return `{content, location, score, metadata}` and accept Bedrock-style filters (`{"equals": {"key": "industry", ...}}`), which `local.to_chroma_where` translates.
- Generation is always `services/llm_service.py`: `client.beta.messages.stream(...).get_final_message()`, `CLAUDE_MODEL` (default `claude-sonnet-5-5`), `output_config.effort`, and `fallbacks="default"` with the `server-side-fallback-2026-07-01` beta. It sends no temperature or top_p, since current models reject them. Only `text` blocks are returned, as `{"output": {"text": ...}}`.

### The industry YAMLs drive everything
`backend/scraper-lambda/src/config/sources/<industry>.yaml` (fields documented in `_defaults.yaml`) defines what is scraped, and every scraped document gets a `<file>.metadata.json` sidecar (`industry`, `sections`, `year`). The same files are read by the orchestrator's `services/industry_config.py`:
- `usages[].section` sets the report sections (`SECTION_TEMPLATES`).
- The top-level `nace_codes` maps a client's NACE code to an industry (`industry_for_nace`). These must match `frontend/src/lib/industries.ts`.

The indexer (`src/retrieval/indexer.py`) copies the sidecar metadata onto every chunk. Chroma metadata must be scalar, so list fields are comma-joined.

### Report flow
- **Market Analysis.**
  - Crops: `handle_market_analysis` with `utils/query_builder.py`, saved to `market_analysis/`.
  - Industries: an event with `industry` goes to `handle_industry_market_analysis` with `utils/industry_retrieval.py`, saved to `industry_analysis/<industry>/`, or to `market_analysis/` with `show_in_frontend`.
  - The frontend reads `GET /analyses/<category>`: an industry id reads `industry_analysis/<id>/`, anything else reads `market_analysis/`.
- **Market Position:** `POST /analyses` with `analysis_type: market_position`. Claude reads the client PDF as a `document` block. Without `market_analysis_key`, the handler uses the latest analysis for the client's industry.
- **Peer Analysis:** the form uploads `<analysis_id>.xlsx`, which trigger-upload converts to `peer_data/<analysis_id>.csv` (keeping cells as text, so AOP codes like `0059` survive). The upload server then POSTs an S3 `ObjectCreated` event to the orchestrator's `/_events/s3`. `lambda_handler` turns it into a peer analysis linked to `market_position/<analysis_id>.json`, and the sector name comes from that report's NACE code (`_peer_sector`).
- The analysis period is the last `ANALYSIS_YEARS_BACK` (2) completed years. The orchestrator's `config/settings.py` and the scraper's `core/period.py` must agree.

### Frontend
Next.js 16 App Router, MUI 7, Tailwind 3, TanStack Query and nuqs. All API calls are in `src/lib/api.ts`. In dev the browser calls `/api-proxy/*`, and `next.config.ts` rewrites it: `/upload` and `/local-upload/*` go to :8002, everything else to :8001, with `experimental.proxyTimeout` raised because report generation takes minutes. Base URLs are in `src/lib/apiUrl.ts` (`NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_UPLOAD_API_URL`). DOCX export happens client-side in `src/utils/generateClientPositionDocx.ts`.

### Text extraction notes
- PDFs: `pymupdf4llm<2`. Version 2.x is an empty placeholder package.
- `.doc` files need macOS `textutil` or `antiword`.
- `.xls` files use `xlrd`.
- Scanned PDFs yield almost no text and are logged as warnings.
