"""
Scraper for government statistical data tables (CSV files).
Source: Statistical Office of the Republic of Serbia - https://data.stat.gov.rs/

Downloads crop production statistics via CSV export.
Files are organized by file type.
"""
import csv
import io
import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class StatisticsScraper:
    """Scraper for government statistical data tables (CSV files)."""

    # Storage path configuration
    SOURCE_CATEGORY = "statistics"

    BASE_URL = "https://data.stat.gov.rs"

    # Target crop products (filter to only these by default)
    # Note: "Maize" is the same as "corn" in English naming
    DEFAULT_PRODUCTS = ["Wheat", "Maize", "Sunflower", "Soya"]

    # Column name mappings
    METRIC_MAPPINGS = {
        "harvested area": "harvested_area_ha",
        "area harvested": "harvested_area_ha",
        "harvested_area": "harvested_area_ha",
        "arvested area": "harvested_area_ha",
        "production area": "harvested_area_ha",
        "total yield": "total_yield_t",
        "yield total": "total_yield_t",
        "production": "total_yield_t",
        "yield per hectare": "yield_per_ha",
        "yield/ha": "yield_per_ha",
        "yield, t/ha": "yield_per_ha",
        "average yield": "yield_per_ha",
    }

    def __init__(self, s3_bucket: str):
        self.s3_bucket = s3_bucket
        self.client = httpx.Client(
            timeout=60.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        import boto3
        self.s3_client = boto3.client("s3")

    def _s3_key_exists(self, s3_key: str) -> bool:
        """Check if an S3 key already exists."""
        if not self.s3_client or not self.s3_bucket:
            return False
        try:
            self.s3_client.head_object(Bucket=self.s3_bucket, Key=s3_key)
            logger.info(f"File exists in S3: {s3_key}")
            return True
        except Exception as e:
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
            if error_code != '404':
                logger.warning(f"S3 head_object error for {s3_key}: {error_code} - {e}")
            return False

    def _get_s3_key(self, dataset_id: str) -> str:
        """Generate deterministic S3 key for a dataset."""
        return f"markdown/{self.SOURCE_CATEGORY}/tables/crop_statistics_{dataset_id}.md"

    def scrape_crop_statistics(
        self,
        result_url: str,
        years: Optional[list[int]] = None,
        products: Optional[list[str]] = None
    ) -> Optional[dict]:
        """
        Scrape crop statistics by downloading CSV export.

        Args:
            result_url: The stat.gov.rs Result URL (from browser)
            years: Optional list of years to filter
            products: Optional list of products to filter

        Returns:
            Metadata dict with file location, or None if failed
        """
        # Extract dataset ID for deterministic S3 key
        dataset_id = result_url if result_url.isdigit() else result_url.rstrip("/").split("/")[-1]

        # Check if file already exists in S3
        if self.s3_bucket:
            s3_key = self._get_s3_key(dataset_id)
            if self._s3_key_exists(s3_key):
                logger.info(f"Skipping (exists): crop_statistics_{dataset_id}.md")
                return {"s3_key": s3_key, "status": "skipped", "reason": "already exists"}

        # Use default products if not specified
        if products is None:
            products = self.DEFAULT_PRODUCTS
            logger.info(f"Using default products filter: {products}")

        logger.info(f"Scraping crop statistics from: {result_url}")

        # Build CSV export URL
        csv_url = self._build_export_url(result_url, format_type="CSV")
        logger.info(f"CSV export URL: {csv_url}")

        # Download CSV
        try:
            csv_response = self.client.get(csv_url)
            csv_response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"Failed to download CSV: {e}")
            return None

        # Decode CSV content with encoding fallbacks
        encodings_to_try = ["utf-8", "latin-1", "cp1252", "utf-16"]
        text = None

        for encoding in encodings_to_try:
            try:
                text = csv_response.content.decode(encoding)
                logger.debug(f"Successfully decoded CSV with {encoding}")
                break
            except (UnicodeDecodeError, LookupError) as e:
                logger.debug(f"Failed to decode with {encoding}: {e}")
                continue

        if text is None:
            logger.error(f"Failed to decode CSV: tried encodings {encodings_to_try}")
            return None

        # Parse CSV structure
        try:
            reader = csv.DictReader(io.StringIO(text), delimiter=";")
            rows = list(reader)
            columns = reader.fieldnames or []
        except csv.Error as e:
            logger.error(f"Failed to parse CSV structure (malformed CSV): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing CSV: {type(e).__name__}: {e}")
            return None

        if not rows:
            logger.error("No data parsed from CSV")
            return None

        logger.info(f"Parsed CSV with {len(rows)} rows and columns: {columns}")

        # Extract and structure the data
        data = self._extract_crop_data(rows, columns, years=years, products=products)

        if not data or not data.get("records"):
            logger.error("No crop data extracted")
            return None

        logger.info(f"Extracted {len(data['records'])} records")

        # Create markdown and save
        md_content = self._create_markdown(data)

        return self._save_output(md_content=md_content, data=data, dataset_id=dataset_id)

    def _build_export_url(self, result_url: str, format_type: str = "CSV") -> str:
        """Build export URL from a result page URL."""
        from urllib.parse import urlparse, parse_qs

        if result_url.isdigit():
            dataset_id = result_url
            lang = "en-US"
        else:
            parsed = urlparse(result_url)
            qs = parse_qs(parsed.query)
            path_parts = parsed.path.rstrip("/").split("/")
            dataset_id = path_parts[-1] if path_parts else ""
            lang = qs.get("languageCode", ["en-US"])[0]

        display_mode = f"export{format_type}"

        return (
            f"{self.BASE_URL}/Home/DisplayResult"
            f"?languageCode={lang}"
            f"&displayMode={display_mode}"
            f"&subAreaId={dataset_id}"
        )

    def _extract_crop_data(
        self,
        rows: list[dict],
        columns: list[str],
        years: Optional[list[int]] = None,
        products: Optional[list[str]] = None
    ) -> dict:
        """Extract structured crop data from CSV rows."""
        records = []
        found_products = set()
        found_years = set()

        # Normalize column names
        col_mapping = {col: col.strip().lower() for col in columns}
        normalized_cols = list(col_mapping.values())
        logger.info(f"Columns: {normalized_cols}")

        year_col = self._find_column(normalized_cols, ["nvrtacka", "year", "godina", "period"])
        product_col = self._find_column(normalized_cols, ["nproizvod", "product", "proizvod", "crop"])
        indicator_col = self._find_column(normalized_cols, ["nvrpod", "indicator", "pokazatelj"])
        value_col = self._find_column(normalized_cols, ["vrednost", "value", "amount"])

        # Create reverse mapping to get original column names
        reverse_mapping = {v: k for k, v in col_mapping.items()}

        logger.info(f"Detected columns - year: {year_col}, product: {product_col}, "
                   f"indicator: {indicator_col}, value: {value_col}")

        if not all([year_col, product_col, value_col]):
            logger.error("Could not identify required columns")
            return {"records": [], "products": [], "years": [],
                    "scraped_at": datetime.now(timezone.utc).isoformat()}

        # Get original column names for lookups
        year_key = reverse_mapping.get(year_col, year_col)
        product_key = reverse_mapping.get(product_col, product_col)
        indicator_key = reverse_mapping.get(indicator_col, indicator_col) if indicator_col else None
        value_key = reverse_mapping.get(value_col, value_col)

        for row in rows:
            try:
                year_val = row.get(year_key, "")
                if not year_val or year_val.strip() == "":
                    continue
                year = int(float(str(year_val)))

                if years and year not in years:
                    continue

                product = str(row.get(product_key, "")).strip()
                if not product:
                    continue

                if products:
                    product_lower = product.lower()
                    if product_lower not in [p.lower() for p in products]:
                        continue

                indicator = str(row.get(indicator_key, "")).strip() if indicator_key else ""
                value = row.get(value_key, "")

                if not value or str(value).strip() == "":
                    continue

                try:
                    if isinstance(value, str):
                        value = float(value.replace(",", ".").replace(" ", ""))
                    else:
                        value = float(value)
                except (ValueError, TypeError):
                    logger.debug(f"Could not convert value: {value}")
                    continue

                metric = self._normalize_metric(indicator)
                records.append({
                    "year": year,
                    "product": product,
                    "metric": metric,
                    "value": value,
                    "indicator_raw": indicator
                })
                found_products.add(product)
                found_years.add(year)

            except Exception as e:
                logger.debug(f"Skipping row: {e}")
                continue

        logger.info(f"Extracted {len(records)} records")

        return {
            "records": records,
            "products": sorted(found_products),
            "years": sorted(found_years),
            "scraped_at": datetime.now(timezone.utc).isoformat()
        }

    def _find_column(self, columns: list[str], candidates: list[str]) -> Optional[str]:
        """Find a column matching any of the candidate names."""
        for col in columns:
            col_lower = str(col).lower()
            for candidate in candidates:
                if candidate in col_lower:
                    return col
        return None

    def _normalize_metric(self, raw: str) -> str:
        """Normalize metric name to standard format."""
        raw_lower = raw.lower()
        for pattern, normalized in self.METRIC_MAPPINGS.items():
            if pattern in raw_lower:
                return normalized
        return raw_lower.replace(" ", "_").replace(",", "")

    def _create_markdown(self, data: dict) -> str:
        """Create markdown content optimized for RAG chunking."""
        lines = [
            "# Serbian Crop Production Statistics",
            "",
            "Source: Statistical Office of the Republic of Serbia (data.stat.gov.rs)",
            f"Years: {', '.join(str(y) for y in data['years'])}",
            f"Products: {', '.join(data['products'])}",
            f"Scraped: {data['scraped_at']}",
            "",
        ]

        by_product = defaultdict(lambda: defaultdict(dict))

        for rec in data["records"]:
            by_product[rec["product"]][rec["year"]][rec["metric"]] = rec["value"]

        for product in sorted(by_product.keys()):
            lines.append(f"## {product} Production in Serbia")
            lines.append("")

            for year in sorted(by_product[product].keys()):
                metrics = by_product[product][year]
                lines.append(f"### {product} - {year}")
                lines.append("")

                if "harvested_area_ha" in metrics:
                    lines.append(f"- **Harvested Area:** {metrics['harvested_area_ha']:,.0f} hectares")
                if "total_yield_t" in metrics:
                    lines.append(f"- **Total Yield:** {metrics['total_yield_t']:,.0f} tonnes")
                if "yield_per_ha" in metrics:
                    val = metrics["yield_per_ha"]
                    if isinstance(val, (int, float)):
                        lines.append(f"- **Yield per Hectare:** {val:.2f} t/ha")
                    else:
                        lines.append(f"- **Yield per Hectare:** {val} t/ha")

                for metric, value in metrics.items():
                    if metric not in ["harvested_area_ha", "total_yield_t", "yield_per_ha"]:
                        if isinstance(value, float):
                            lines.append(f"- **{metric.replace('_', ' ').title()}:** {value:,.2f}")
                        else:
                            lines.append(f"- **{metric.replace('_', ' ').title()}:** {value}")

                lines.append("")

        lines.extend([
            "---",
            "",
            "Source: Statistical Office of the Republic of Serbia (RZS)"
        ])

        return "\n".join(lines)

    def _save_output(
        self,
        md_content: str,
        data: dict,
        dataset_id: str
    ) -> dict:
        """Save markdown file to S3 with deterministic key (for deduplication)."""
        content_bytes = md_content.encode("utf-8")
        years_str = "_".join(str(y) for y in data["years"])

        # Structure: markdown/statistics/tables/crop_statistics_{dataset_id}.md
        md_key = self._get_s3_key(dataset_id)

        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=md_key,
            Body=content_bytes,
            ContentType="text/markdown; charset=utf-8",
            Metadata={
                "source": "data.stat.gov.rs",
                "source_category": self.SOURCE_CATEGORY,
                "dataset_id": dataset_id,
                "years": years_str
            }
        )

        logger.info(f"Uploaded to S3: {md_key}")

        return {
            "s3_key": md_key,
            "file_type": "markdown",
            "years": data["years"],
            "products": data["products"],
            "record_count": len(data["records"])
        }

    def close(self):
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
