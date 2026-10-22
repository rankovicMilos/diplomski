"""
Excel to CSV processor.
Supports both .xlsx and .xls formats.
"""
import io
import logging
from dataclasses import dataclass

import pandas as pd

from src.config import SUPPORTED_EXCEL_EXTENSIONS

logger = logging.getLogger(__name__)

# Security limit
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@dataclass
class ProcessingResult:
    """Result of Excel to CSV processing."""

    csv_content: bytes
    original_filename: str
    output_filename: str
    rows_processed: int
    sheets_processed: int


class ExcelProcessor:
    """Processor for converting Excel files to CSV."""

    def is_supported_excel_file(self, filename: str) -> bool:
        """Check if the file is a supported Excel format."""
        lower_filename = filename.lower()
        return any(lower_filename.endswith(ext) for ext in SUPPORTED_EXCEL_EXTENSIONS)

    def process_excel_to_csv(
        self,
        excel_content: bytes,
        filename: str,
        sheet_name: str | int | None = 0,
    ) -> ProcessingResult:
        """
        Convert Excel file content to CSV.

        Args:
            excel_content: Raw bytes of the Excel file
            filename: Original filename (used to determine format and output name)
            sheet_name: Sheet to convert (default: first sheet).
                       Use None to convert all sheets into one CSV.

        Returns:
            ProcessingResult with CSV content and metadata

        Raises:
            ValueError: If the file format is not supported
            Exception: If processing fails
        """
        if not self.is_supported_excel_file(filename):
            raise ValueError(
                f"Unsupported file format: {filename}. "
                f"Supported formats: {SUPPORTED_EXCEL_EXTENSIONS}"
            )

        if len(excel_content) > MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {len(excel_content)} bytes (max: {MAX_FILE_SIZE} bytes / 10 MB)"
            )

        lower_filename = filename.lower()
        engine = "openpyxl" if lower_filename.endswith(".xlsx") else "xlrd"

        logger.info(f"Processing {filename} using engine: {engine}")

        excel_buffer = io.BytesIO(excel_content)

        if sheet_name is None:
            df = self._read_all_sheets(excel_buffer, engine)
            sheets_processed = len(pd.ExcelFile(io.BytesIO(excel_content), engine=engine).sheet_names)
        else:
            # dtype=str keeps codes such as AOP "0059" as written (no numeric coercion)
            df = pd.read_excel(excel_buffer, sheet_name=sheet_name, engine=engine, dtype=str)
            sheets_processed = 1

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue().encode("utf-8")

        output_filename = self._generate_csv_filename(filename)

        logger.info(
            f"Processing complete: {filename} -> {output_filename}, "
            f"rows: {len(df)}, sheets: {sheets_processed}"
        )

        return ProcessingResult(
            csv_content=csv_content,
            original_filename=filename,
            output_filename=output_filename,
            rows_processed=len(df),
            sheets_processed=sheets_processed,
        )

    def _read_all_sheets(self, excel_buffer: io.BytesIO, engine: str) -> pd.DataFrame:
        """Read all sheets from an Excel file and concatenate them."""
        excel_file = pd.ExcelFile(excel_buffer, engine=engine)
        dfs = []
        for sheet in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet, dtype=str)
            dfs.append(df)
        return pd.concat(dfs, ignore_index=True)

    def _generate_csv_filename(self, original_filename: str) -> str:
        """Generate CSV filename from original Excel filename."""
        base_name = original_filename.rsplit(".", 1)[0]
        return f"{base_name}.csv"


# Singleton instance for Lambda reuse
excel_processor = ExcelProcessor()
