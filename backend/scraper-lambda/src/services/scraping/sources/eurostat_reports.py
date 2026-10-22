"""
Scraper for Eurostat regional yearbook (PDF files).
Source: https://ec.europa.eu/eurostat/web/main/publications/flagship-publications

Downloads the Eurostat regional yearbook PDF publications.
Files are organized by year in the pdf/eurostat_reports/ directory.
"""
import re
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote, urljoin

import httpx

logger = logging.getLogger(__name__)


class EurostatScraper:
    """Scraper for Eurostat regional yearbook PDF reports."""

    # Storage path configuration
    SOURCE_CATEGORY = "eurostat_reports"
    BASE_URL = "https://ec.europa.eu/eurostat/web/main/publications/flagship-publications"

    # Default years to scrape
    DEFAULT_YEARS = [2024, 2025]

    # Publication title pattern to match
    YEARBOOK_TITLE_PATTERN = r"Eurostat regional yearbook"

    def __init__(self, s3_bucket: str):
        """
        Initialize scraper.

        Args:
            s3_bucket: S3 bucket for uploads
        """
        self.s3_bucket = s3_bucket
        self.client = httpx.Client(timeout=120.0, follow_redirects=True)

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
        Scrape Eurostat regional yearbook PDFs.

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

        # Find all yearbook publication links
        publications = self._find_yearbook_links(soup)

        if not publications:
            logger.warning("No Eurostat regional yearbook publications found")
            return []

        logger.info(f"Found {len(publications)} yearbook publications")

        # Use default years if not specified
        if years is None:
            years = self.DEFAULT_YEARS
            logger.info(f"Using default years filter: {years}")

        # Filter by years
        publications = self._filter_by_years(publications, years)
        logger.info(f"After year filter ({years}): {len(publications)} publications")

        # Apply limit
        if limit:
            publications = publications[:limit]

        # Download files
        downloaded = []
        skipped = 0

        for pub in publications:
            pub_url = pub["url"]
            pub_title = pub["title"]
            pub_year = pub["year"]

            clean_name = self._clean_filename(pub_title)
            s3_key = f"pdf/{self.SOURCE_CATEGORY}/{pub_year}/{clean_name}.pdf"

            # Check if file already exists in S3
            if self._s3_key_exists(s3_key):
                logger.info(f"Skipping (exists): {clean_name}.pdf")
                skipped += 1
                continue

            # Download file
            logger.info(f"Processing: {pub_title}")
            result = self._download_publication(
                publication_url=pub_url,
                title=pub_title,
                year=pub_year,
                clean_name=clean_name
            )
            if result:
                downloaded.append(result)
                logger.info(f"  Uploaded: {result.get('s3_key')}")

        logger.info(f"Complete: {len(downloaded)} new, {skipped} skipped")
        return downloaded

    def _find_yearbook_links(self, soup) -> list[dict]:
        """
        Find all Eurostat regional yearbook publication links on the page.

        Looks for links containing "Eurostat regional yearbook" in their title.
        """
        items = []

        # Find all article links that might contain yearbook publications
        # The structure is: <a href="..."><article>...<div class="ecl-content-block__title">Title</div>...</article></a>
        links = soup.find_all("a", href=re.compile(r"/products-flagship-publications/"))

        for link in links:
            href = link.get("href", "")

            # Find the title within this link
            title_div = link.find(class_="ecl-content-block__title")
            if not title_div:
                # Also try finding any text that matches yearbook pattern
                title_text = link.get_text(strip=True)
            else:
                title_text = title_div.get_text(strip=True)

            # Check if this is a regional yearbook
            if not re.search(self.YEARBOOK_TITLE_PATTERN, title_text, re.IGNORECASE):
                continue

            # Extract year from title (e.g., "2025 edition")
            year = self._extract_year_from_title(title_text)

            # Build full URL
            full_url = urljoin("https://ec.europa.eu", href)

            items.append({
                "url": full_url,
                "title": title_text,
                "year": year
            })
            logger.debug(f"Found yearbook: {title_text} (year: {year})")

        return items

    def _extract_year_from_title(self, title: str) -> int:
        """
        Extract year from title.

        Format: "Eurostat regional yearbook – 2025 edition"
        """
        # Look for 4-digit year
        match = re.search(r'(20\d{2})', title)
        if match:
            return int(match.group(1))

        # Default to current year
        return datetime.now().year

    def _filter_by_years(self, items: list[dict], years: list[int]) -> list[dict]:
        """Filter items by year."""
        return [item for item in items if item.get("year") in years]

    def _get_pdf_download_url(self, publication_page_url: str) -> Optional[str]:
        """
        Extract the PDF download URL from a publication page.

        Looks for: <a href="...pdf...?download=true" class="ecl-link ecl-link--secondary ecl-link--icon">
        """
        try:
            logger.info(f"  Fetching publication page: {publication_page_url}")
            response = self.client.get(publication_page_url)
            response.raise_for_status()

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Look for download link with specific class pattern
            download_link = soup.find("a", class_=re.compile(r"ecl-link.*ecl-link--icon"),
                                      href=re.compile(r"\.pdf.*download=true", re.IGNORECASE))

            if download_link:
                href = download_link.get("href", "")
                logger.debug(f"Found download link: {href}")
                if href.startswith("http"):
                    return href
                return urljoin("https://ec.europa.eu", href)

            # Fallback: look for any PDF download link
            download_link = soup.find("a", href=re.compile(r"\.pdf.*download=true", re.IGNORECASE))
            if download_link:
                href = download_link.get("href", "")
                logger.debug(f"Found download link (fallback): {href}")
                if href.startswith("http"):
                    return href
                return urljoin("https://ec.europa.eu", href)

            # Second fallback: any PDF link
            download_link = soup.find("a", href=re.compile(r"\.pdf", re.IGNORECASE))
            if download_link:
                href = download_link.get("href", "")
                # Add download=true if not present
                if "download=true" not in href:
                    href = href + ("&" if "?" in href else "?") + "download=true"
                logger.debug(f"Found PDF link (second fallback): {href}")
                if href.startswith("http"):
                    return href
                return urljoin("https://ec.europa.eu", href)

            logger.warning(f"Could not find PDF download link on page: {publication_page_url}")
            return None

        except Exception as e:
            logger.error(f"Failed to get PDF URL from {publication_page_url}: {e}")
            return None

    def _download_publication(
        self,
        publication_url: str,
        title: str,
        year: int,
        clean_name: str
    ) -> Optional[dict]:
        """Download PDF from publication page and upload to S3."""
        try:
            # First, get the actual PDF URL from the publication page
            pdf_url = self._get_pdf_download_url(publication_url)
            if not pdf_url:
                logger.error(f"Could not resolve PDF URL for: {title}")
                return None

            logger.info(f"  Downloading PDF from: {pdf_url[:100]}...")

            # Download the PDF (these can be large files)
            response = self.client.get(pdf_url)
            response.raise_for_status()

            content = response.content

            # Verify it's actually a PDF
            if not content.startswith(b'%PDF'):
                logger.warning(f"File is not a PDF: {title} (got {len(content)} bytes)")
                return None

            logger.info(f"  Downloaded {len(content) / 1024 / 1024:.1f} MB")

            return self._upload_to_s3(
                content=content,
                file_year=year,
                clean_name=clean_name,
                file_url=pdf_url,
                original_name=title
            )

        except Exception as e:
            logger.error(f"Failed to download {title}: {e}")
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
        # Replace spaces and dashes with underscores
        clean = clean.replace(' ', '_').replace('–', '-').replace('—', '-')
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
