"""
Turn a downloaded CSV export into a clean table.

Used for every CSV a scraper downloads (RZS, Eurostat, ...). All options are generic and
come from the source's `params.csv` (often through a preset in _defaults.yaml):

  delimiter:       column separator; detected when omitted (; , tab)
  drop_columns:    regex; columns whose name matches are removed (code/status columns)
  rename_columns:  {old name: new name}
  row_filter:      regex; keep only rows where some cell matches (case-insensitive)
  period_column:   column with the period (name before or after renaming); only rows from
                   the analysis period are kept (core/period.py). null keeps all years
  max_rows:        cap on rows (default 5000)
"""
import csv
import io
import re
from typing import Any

from .exceptions import FetchError
from .models import DataTable
from .period import analysis_years, years_in

DEFAULT_MAX_ROWS = 5000
CANDIDATE_DELIMITERS = ";,\t"


def parse_csv(content: bytes, title: str, url: str, options: dict[str, Any]) -> DataTable:
    text = _decode(content)
    delimiter = options.get("delimiter") or _detect_delimiter(text)
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=delimiter) if any(r)]
    if len(rows) < 2:
        raise FetchError("CSV has no data rows", url=url)

    header, data = rows[0], rows[1:]
    notes: list[str] = []

    if options.get("period_column"):
        data = _filter_period(header, data, options, notes, url)

    if options.get("row_filter"):
        pattern = re.compile(options["row_filter"], re.IGNORECASE)
        total = len(data)
        data = [r for r in data if any(pattern.search(cell) for cell in r)]
        notes.append(f"Filtered to {len(data)} of {total} rows ({options['row_filter']})")
        if not data:
            raise FetchError(f"row_filter matched none of {total} rows", url=url)

    keep = list(range(len(header)))
    if options.get("drop_columns"):
        drop = re.compile(options["drop_columns"])
        keep = [i for i in keep if not drop.search(header[i])]

    max_rows = int(options.get("max_rows", DEFAULT_MAX_ROWS))
    if len(data) > max_rows:
        notes.append(f"Truncated to {max_rows} of {len(data)} rows")
        data = data[:max_rows]

    renames = options.get("rename_columns") or {}
    return DataTable(
        title=title,
        columns=[renames.get(header[i], header[i]) for i in keep],
        rows=[[row[i] if i < len(row) else "" for i in keep] for row in data],
        source_url=url,
        notes=notes,
    )


def _filter_period(
    header: list[str], data: list[list[str]], options: dict[str, Any], notes: list[str], url: str
) -> list[list[str]]:
    """Keep rows whose period falls in the analysis period; rows without a year stay."""
    column = options["period_column"]
    renames = options.get("rename_columns") or {}
    index = next((i for i, h in enumerate(header) if column in (h, renames.get(h))), None)
    if index is None:
        raise FetchError(f"period_column '{column}' not in CSV columns {header}", url=url)

    years = set(analysis_years())
    period = f"{min(years)}-{max(years)}"
    kept = []
    for row in data:
        found = years_in(row[index]) if index < len(row) else []
        if not found or any(y in years for y in found):
            kept.append(row)
    if kept:
        notes.append(f"Period {period}: kept {len(kept)} of {len(data)} rows")
    else:
        notes.append(f"No data for {period} in the source ({len(data)} rows from other years)")
    return kept


def _decode(content: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1250"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _detect_delimiter(text: str) -> str:
    sample = "\n".join(text.splitlines()[:20])
    try:
        return csv.Sniffer().sniff(sample, delimiters=CANDIDATE_DELIMITERS).delimiter
    except csv.Error:
        first_line = sample.splitlines()[0] if sample else ""
        return max(CANDIDATE_DELIMITERS, key=first_line.count)
