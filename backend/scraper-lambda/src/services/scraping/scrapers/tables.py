"""Rendering DataTable objects as markdown and CSV."""
import csv
import io

from ..core.models import DataTable
from ..core.text_extractor import rows_to_markdown


def table_to_markdown(table: DataTable, heading_level: int = 2) -> str:
    parts = [f"{'#' * heading_level} {table.title}"]
    if table.notes:
        parts.append("\n".join(f"- {note}" for note in table.notes))
    parts.append(rows_to_markdown([[str(c) for c in r] for r in table.rows], header=table.columns))
    return "\n\n".join(parts)


def rows_to_csv(header: list[str], rows: list[list]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    if header:
        writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()
