# Sector Risk Analysis

AI-assisted sector and credit risk analysis: the system collects public market data for an
industry, indexes it, and uses Claude to write a **Market Analysis** of the industry and,
from a client's financial statements, a **Market Position** report and a **Peer Analysis**.
Domain terms are defined in [CONTEXT.md](./CONTEXT.md).

Bachelor thesis project. _Author, faculty and mentor: to be added._

**Focus:** Serbian market — industries are configured in YAML (electricity and cereals are
the demonstrated ones; 15 are configured).

## Architecture

```
            ┌────────────┐   documents +    ┌──────────────┐  chunks +  ┌──────────────┐
 public ───▶│  Scraper   │──── metadata ───▶│  Indexer     │─ vectors ─▶│ Vector index │
 sources    │ (YAML per  │   (data/…raw)    │ (text, chunk,│            │  (Chroma)    │
            │  industry) │                  │  embed)      │            └──────┬───────┘
            └────────────┘                  └──────────────┘                   │ retrieve
                                                                               ▼
 ┌──────────┐  HTTP   ┌──────────────┐   prompt + retrieved context   ┌──────────────┐
 │ Next.js  │────────▶│ Orchestrator │───────────────────────────────▶│ Claude (API) │
 │ frontend │◀────────│ (reports)    │◀──────────── JSON report ──────└──────────────┘
 └──────────┘         └──────────────┘
      │ upload PDF/Excel      ▲ peer CSV triggers peer analysis
      ▼                       │
 ┌──────────────┐  CSV  ─────┘
 │ Upload       │
 └──────────────┘
```

The components are AWS Lambda functions. The original deployment ran them on AWS (API
Gateway, S3, Bedrock Knowledge Base — see [infrastructure/](./infrastructure/README.md));
this project runs the **same handlers locally**, with switchable backends:

| Concern | Local (default) | AWS (original) |
|---|---|---|
| Generation | Claude via Anthropic API | Claude via Anthropic API |
| Retrieval | Chroma + `BAAI/bge-m3` embeddings (`RETRIEVAL_BACKEND=local`) | Bedrock Knowledge Base (`bedrock`) |
| Storage | folders under `data/` (`STORAGE_BACKEND=local`) | S3 (`s3`) |
| HTTP | `local_server.py` per Lambda (FastAPI) | API Gateway |

## Project structure

```
backend/
├── scraper-lambda/          # config-driven scrapers; sources in src/config/sources/<industry>.yaml
├── orchestrator-lambda/     # report generation, retrieval (src/retrieval), local API server
└── trigger-upload-lambda/   # client file uploads (PDF; Excel -> CSV), local upload server
frontend/                    # Next.js 16 web app
infrastructure/              # Terraform for the AWS deployment (reference only)
scripts/                     # dev.sh (run everything), demo.sh (collect data + market analysis)
demo-data/                   # how to prepare client and peer files for a demo
```

## Running locally

Prerequisites: Python 3.11+, [uv](https://docs.astral.sh/uv/), Node.js 20+, an Anthropic API key.

```bash
cp .env.example .env              # set ANTHROPIC_API_KEY
(cd frontend && npm install)

scripts/dev.sh                    # orchestrator :8001, upload :8002, frontend http://localhost:3000
```

In a second terminal, collect data and generate the market analyses:

```bash
scripts/demo.sh electricity       # scrape -> index -> industry market analysis
scripts/demo.sh cereals           # scrape -> index -> crop market analysis
```

The first indexing run downloads the embedding model (~2 GB). Then open the app, choose an
industry, and create a client report by uploading the client's financial statements (PDF)
and a peer Excel file (see [demo-data/](./demo-data/README.md)).

## Data sources

Public sources per industry, e.g. Ministry of Agriculture market reports, the Novi Sad
commodity exchange, the Statistical Office of Serbia (RZS), AERS and EPS annual reports,
Eurostat and the Energy Community. The full list is in
`backend/scraper-lambda/src/config/sources/`.

## Documentation

- [Backend](./backend/README.md) — services, local run, tests
- [Frontend](./frontend/README.md)
- [Infrastructure](./infrastructure/README.md) — the AWS reference architecture
- [CONTEXT.md](./CONTEXT.md) — domain glossary
