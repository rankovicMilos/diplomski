"""
Scraper for Zita Srbije monthly reports (PDF files).
Source: https://www.zitasrbije.rs/tekst.php?grupaA=13

Downloads monthly grain market reports from the Serbian Grain Association.
Files are organized by year in the pdf/zitasrbije_reports/ directory.
"""
import re
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote, urljoin

import httpx

logger = logging.getLogger(__name__)


class ZitaSrbijeScraper:
    """Scraper for Zita Srbije monthly PDF reports."""

    # Storage path configuration
    SOURCE_CATEGORY = "zitasrbije_reports"
    BASE_URL = "https://www.zitasrbije.rs/tekst.php?grupaA=13"

    # Default years to scrape
    DEFAULT_YEARS = [2024, 2025]

    def __init__(self, s3_bucket: str):
        """
        Initialize scraper.

        Args:
            s3_bucket: S3 bucket for uploads
        """
        self.s3_bucket = s3_bucket
        self.client = httpx.Client(timeout=60.0, follow_redirects=True)

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
            if error_code == '404':
                logger.debug(f"File not found in S3: {s3_key}")
            else:
                logger.warning(f"S3 head_object error for {s3_key}: {error_code} - {e}")
            return False

    def scrape_reports(
        self,
        years: Optional[list[int]] = None,
        limit: Optional[int] = None
    ) -> list[dict]:
        """
        Scrape PDF reports from Zita Srbije.

        Args:
            years: Filter by years (e.g., [2024, 2025])
            limit: Max files to download (None = unlimited)

        Returns:
            List of downloaded file metadata
        """
        logger.info(f"Fetching page: {self.BASE_URL}")
        response = self.client.get(self.BASE_URL)
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all download links with DOWNLOAD.php pattern
        download_items = self._find_download_links(soup)

        if not download_items:
            logger.warning("No PDF files found on page")
            return []

        logger.info(f"Found {len(download_items)} PDF files")

        # Use default years if not specified
        if years is None:
            years = self.DEFAULT_YEARS
            logger.info(f"Using default years filter: {years}")

        # Filter by years
        download_items = self._filter_by_years(download_items, years)
        logger.info(f"After year filter ({years}): {len(download_items)} files")

        # Apply limit
        if limit:
            download_items = download_items[:limit]

        # Download files
        downloaded = []
        skipped = 0

        for item in download_items:
            file_url = item["url"]
            file_name = item["name"]
            file_year = item["year"]

            clean_name = self._clean_filename(file_name)
            s3_key = f"pdf/{self.SOURCE_CATEGORY}/{file_year}/{clean_name}.pdf"

            # Check if file already exists in S3
            if self.s3_bucket and self._s3_key_exists(s3_key):
                logger.info(f"Skipping (exists): {clean_name}.pdf")
                skipped += 1
                continue

            # Download file
            logger.info(f"Downloading: {file_name}")
            result = self._download_file(
                file_url=file_url,
                file_name=file_name,
                file_year=file_year,
                clean_name=clean_name
            )
            if result:
                downloaded.append(result)
                logger.info(f"  Uploaded: {result.get('s3_key')}")

        logger.info(f"Complete: {len(downloaded)} new, {skipped} skipped")
        return downloaded

    def _find_download_links(self, soup) -> list[dict]:
        """
        Find all PDF download links on the page.

        Looks for: <a href="DOWNLOAD.php?o=XXX" title="filename.pdf">
        """
        items = []

        # Find all links with DOWNLOAD.php in href
        download_links = soup.find_all("a", href=re.compile(r"DOWNLOAD\.php\?o=\d+"))

        seen_urls = set()  # Avoid duplicates (same link appears twice on page)

        for link in download_links:
            href = link.get("href", "")
            title = link.get("title", "")

            # Skip if no title or already seen
            if not title or href in seen_urls:
                continue

            seen_urls.add(href)

            # Build full URL
            full_url = urljoin("https://www.zitasrbije.rs/", href)

            # Extract year from title (format: "Mesecni Izvestaj 9.21.pdf" -> 2021)
            year = self._extract_year_from_title(title)

            items.append({
                "url": full_url,
                "name": title,
                "year": year
            })
            logger.debug(f"Found PDF: {title} (year: {year})")

        return items

    def _extract_year_from_title(self, title: str) -> int:
        """
        Extract year from title.

        Formats:
        - "Mesecni Izvestaj 9.21.pdf" -> 2021
        - "Mesecni Izvestaj 12.24.pdf" -> 2024
        """
        # Look for pattern like "9.21" or "12.24" (month.year)
        match = re.search(r'(\d{1,2})\.(\d{2})(?:\.pdf)?', title, re.IGNORECASE)
        if match:
            short_year = int(match.group(2))
            # Convert 2-digit year to 4-digit (21 -> 2021, 24 -> 2024)
            return 2000 + short_year if short_year < 100 else short_year

        # Try 4-digit year
        match = re.search(r'(20\d{2})', title)
        if match:
            return int(match.group(1))

        # Default to current year
        return datetime.now().year

    def _filter_by_years(self, items: list[dict], years: list[int]) -> list[dict]:
        """Filter items by year."""
        return [item for item in items if item.get("year") in years]

    def _get_actual_pdf_url(self, download_page_url: str) -> Optional[str]:
        """
        Extract actual PDF URL from the DOWNLOAD.php intermediate page.

        The DOWNLOAD.php page contains an HTML page with a link to the actual PDF
        at http://www.zitasrbije.rs/download/filename.pdf
        """
        try:
            response = self.client.get(download_page_url)
            response.raise_for_status()

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Look for link to /download/ directory
            pdf_link = soup.find("a", href=re.compile(r"download/.*\.pdf", re.IGNORECASE))
            if pdf_link:
                href = pdf_link.get("href", "")
                return urljoin("https://www.zitasrbije.rs/", href)

            # Fallback: look for any .pdf link
            pdf_link = soup.find("a", href=re.compile(r"\.pdf$", re.IGNORECASE))
            if pdf_link:
                href = pdf_link.get("href", "")
                return urljoin("https://www.zitasrbije.rs/", href)

            logger.warning(f"Could not find PDF link on page: {download_page_url}")
            return None

        except Exception as e:
            logger.error(f"Failed to get PDF URL from {download_page_url}: {e}")
            return None

    def _download_file(
        self,
        file_url: str,
        file_name: str,
        file_year: int,
        clean_name: str
    ) -> Optional[dict]:
        """Download PDF file and upload to S3."""
        try:
            # First, get the actual PDF URL from the intermediate page
            actual_pdf_url = self._get_actual_pdf_url(file_url)
            if not actual_pdf_url:
                logger.error(f"Could not resolve actual PDF URL for: {file_name}")
                return None

            logger.info(f"  Resolved PDF URL: {actual_pdf_url}")

            # Now download the actual PDF
            response = self.client.get(actual_pdf_url)
            response.raise_for_status()

            content = response.content

            # Verify it's actually a PDF
            if not content.startswith(b'%PDF'):
                logger.warning(f"File is not a PDF: {file_name} (got {len(content)} bytes)")
                return None

            return self._upload_to_s3(
                content=content,
                file_year=file_year,
                clean_name=clean_name,
                file_url=actual_pdf_url,
                original_name=file_name
            )

        except Exception as e:
            logger.error(f"Failed to download {file_url}: {e}")
            return None

    def _upload_to_s3(
        self,
        content: bytes,
        file_year: int,
        clean_name: str,
        file_url: str,
        original_name: str
    ) -> dict:
        """Upload file to S3."""
        s3_key = f"pdf/{self.SOURCE_CATEGORY}/{file_year}/{clean_name}.pdf"

        # Truncate original_name to avoid metadata limit
        truncated_name = original_name[:50] if len(original_name) > 50 else original_name

        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=s3_key,
            Body=content,
            ContentType="application/pdf",
            Metadata={
                "source_url": file_url[:200],
                "source_category": self.SOURCE_CATEGORY,
                "year": str(file_year),
                "original_name": quote(truncated_name, safe=""),
                "scraped_at": datetime.now(timezone.utc).isoformat()
            }
        )

        logger.info(f"Uploaded: s3://{self.s3_bucket}/{s3_key}")

        return {
            "s3_key": s3_key,
            "source_url": file_url,
            "file_name": original_name,
            "file_type": "pdf",
            "year": file_year,
            "size_bytes": len(content)
        }

    def _clean_filename(self, name: str) -> str:
        """Clean filename for storage."""
        # Remove invalid characters
        clean = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace spaces with underscores
        clean = clean.replace(' ', '_')
        # Remove .pdf extension if present
        clean = re.sub(r'\.pdf$', '', clean, flags=re.IGNORECASE)
        # Limit length
        return clean[:100]

    def close(self):
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
