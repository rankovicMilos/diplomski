#!/usr/bin/env bash
# Collect the data for an industry and generate its market analysis.
#
#   scripts/demo.sh electricity     # industry market analysis (industry_analysis/electricity/)
#   scripts/demo.sh cereals         # crop market analysis (market_analysis/)
#
# Steps: scrape the industry's sources -> index them -> generate the report through the
# running orchestrator (start it first with scripts/dev.sh). Pass --skip-scrape to reuse
# already downloaded documents.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INDUSTRY="${1:?usage: scripts/demo.sh <industry> [--skip-scrape]}"
set -a; source "$ROOT/.env"; set +a
DATA_DIR="${LOCAL_DATA_DIR:-$ROOT/data}"
RAW_DIR="$DATA_DIR/${RAW_DATA_BUCKET:-sra-thesis-raw-data}"

if [[ "${2:-}" != "--skip-scrape" ]]; then
  echo "== Scraping $INDUSTRY"
  (cd "$ROOT/backend/scraper-lambda" && \
    uv run python -m src.services.scraping.cli run --industry "$INDUSTRY" --storage local --out "$RAW_DIR")
fi

echo "== Indexing $INDUSTRY"
(cd "$ROOT/backend/orchestrator-lambda" && \
  uv run --extra local-rag python -m src.retrieval.indexer --source "$RAW_DIR" --industry "$INDUSTRY")

if [[ "$INDUSTRY" == "cereals" ]]; then
  BODY='{"analysis_type": "market_analysis"}'
else
  BODY="{\"analysis_type\": \"market_analysis\", \"industry\": \"$INDUSTRY\"}"
fi

echo "== Generating the $INDUSTRY market analysis (takes a few minutes)"
curl -sS --fail-with-body --max-time 900 -X POST http://localhost:8001/analyses \
  -H "Content-Type: application/json" -d "$BODY" \
  | python3 -c "import json,sys; r=json.load(sys.stdin); print('Saved:', r.get('analysis_id'), '| chunks:', r.get('retrieval_stats', {}).get('total_chunks'), '| error:' , r.get('error'))"
