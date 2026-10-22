# Trigger Upload Lambda

AWS Lambda function for handling file uploads with Excel-to-CSV conversion and PDF presigned URL generation.

## Overview

API Gateway-triggered Lambda that processes file uploads:
- **Excel files** (.xlsx, .xls): Converts to CSV and stores in S3
- **PDF files**: Generates presigned URLs for direct S3 upload

## Architecture

```
Client → API Gateway → Lambda → S3
                          ↓
                    Excel Processor
```

## API Endpoints

### POST /upload

**Excel Upload (Base64)**
```json
{
  "filename": "data.xlsx",
  "file_content": "<base64-encoded-content>"
}
```

Response:
```json
{
  "status": "success",
  "csv_key": "peer_data/data_20250130_123456_abc123.csv",
  "bucket": "sra-thesis-client-data"
}
```

**PDF Upload (Presigned URL)**
```json
{
  "filename": "report.pdf"
}
```

Response:
```json
{
  "upload_url": "https://s3.amazonaws.com/...",
  "key": "market_position_data/pdf/report_20250130_123456_abc123.pdf",
  "bucket": "sra-thesis-client-data",
  "expires_in": 3600
}
```

## Configuration

### Environment Variables

Environment variables (override `src/config/config.yaml`):
- `STORAGE_BACKEND`: `local` (default; folders under `LOCAL_DATA_DIR`) or `s3`
- `S3_BUCKET`, `ORCHESTRATOR_DATA_BUCKET` or `CLIENT_DATA_BUCKET`: target bucket
- `LOCAL_UPLOAD_BASE_URL`: base of the local upload URLs (default `http://localhost:3000/api-proxy`)
- `ALLOWED_ORIGIN`: CORS origin (default `http://localhost:3000`)
- `AWS_REGION`: AWS region (default: eu-central-1)
- `PRESIGNED_URL_EXPIRATION`: URL expiration in seconds (default: 3600)

## File Limits

- Max Excel file size: 10 MB
- Supported formats: .xlsx, .xls, .pdf

## S3 Structure

```
{bucket}/
├── market_position_data/
│   ├── pdf/           # PDF uploads
│   └── excel/         # Excel uploads
└── peer_data/         # Converted CSV files
```

## Dependencies

- Python 3.11+
- pandas (Excel processing)
- openpyxl (XLSX support)
- xlrd (XLS support)
- boto3 (S3 operations)
- PyYAML (configuration)

## Project Structure

```
src/
├── config/
│   ├── config.yaml        # Default configuration
│   └── settings.py        # Config loader
├── handlers/
│   └── ingestion.py       # Lambda handler
├── services/
│   ├── excel_processor.py # Excel → CSV conversion
│   └── s3_service.py      # S3 operations
├── utils/
│   └── response.py        # API Gateway responses
└── models/                # Data models
```

## Development

```bash
uv sync --group local
uv run --group local uvicorn local_server:app --port 8002
```

Locally, PDF "presigned" URLs point at the local server (`PUT /local-upload/<key>`), and a CSV
written to `peer_data/` is announced to the orchestrator as an S3 event (`POST /_events/s3`).

## Deployment

Package and deploy using AWS SAM, Terraform, or CDK with runtime Python 3.11+.

Handler: `src.handlers.ingestion.lambda_handler`

## Error Handling

- 400: Invalid request, unsupported format, file too large
- 405: Method not allowed (use POST)
- 500: S3 configuration error, processing failure
