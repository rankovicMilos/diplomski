# Scraper Lambda

AWS Lambda function that scrapes agricultural market reports from multiple Serbian and European sources on a scheduled basis.

## Overview

Automated data collection service triggered by EventBridge or API Gateway. Downloads reports and uploads to S3 for downstream processing.

## Data Sources

| Source | Type | Content |
|--------|------|---------|
| **minpolj** | DOCX/XLSX | Government market reports (corn, wheat, sunflower, soybean) |
| **nscomex** | Markdown | Commodity exchange weekly reports |
| **statgov** | CSV | Government statistical tables |
| **zitasrbije** | PDF | Serbian Grain Association monthly reports |
| **eurostat** | PDF | Eurostat regional yearbook |

## Requirements

- Python 3.11+
- AWS S3 bucket (configured via `RAW_DATA_BUCKET` env var)
- Dependencies: `boto3`, `httpx`, `beautifulsoup4`, `lxml`

## Event Parameters

```json
{
  "source": "minpolj|nscomex|statgov|zitasrbije|eurostat|all",
  "sections": ["corn", "wheat", "sunflower", "soybean"],
  "years": [2024, 2025],
  "limit": 10,
  "result_url": "130102"
}
```

**Parameters:**
- `source`: Target source or "all" (default: "all")
- `sections`: Crop sections for minpolj (default: all)
- `years`: Filter by years (default: [2024, 2025])
- `limit`: Max files per section/source (default: unlimited)
- `result_url`: Dataset ID for statgov (default: "130102")

## S3 Storage Structure

```
s3://{RAW_DATA_BUCKET}/
├── docx/market_reports/{year}/{crop}/
├── xlsx/market_reports/{year}/{crop}/
├── markdown/
│   ├── exchange_reports/{year}/
│   └── statistics/tables/
├── csv/statistics/tables/
└── pdf/
    ├── zitasrbije_reports/{year}/
    └── eurostat_reports/{year}/
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `RAW_DATA_BUCKET` | S3 bucket for storing scraped files | Yes |
| `ALLOWED_ORIGIN` | CORS origin (default: `http://localhost:3000`) | No |
| `MARKET_REPORTS_URL` | Override minpolj base URL | No |

## Config-driven sources

Sources are declared per industry in `src/config/sources/<industry>.yaml`; `_defaults.yaml`
documents every field. Run them locally with the CLI (output mirrors the S3 key layout and
gets a `<file>.metadata.json` sidecar per document):

```bash
uv run python -m src.services.scraping.cli validate
uv run python -m src.services.scraping.cli list --industry electricity --status all
uv run python -m src.services.scraping.cli run --industry cereals --storage local --out ../../data/sra-thesis-raw-data
```

The cereals sources of the original scrapers (`src/services/scraping/sources/`) are migrated to
`cereals.yaml`; the legacy classes are only used by the Lambda's `source` event parameter.

## Development

```bash
uv sync
uv run ruff check src/
```

## Lambda Handler

Entry point: `src.handlers.scraper.lambda_handler`

Supports both scheduled EventBridge triggers and API Gateway requests with CORS.
