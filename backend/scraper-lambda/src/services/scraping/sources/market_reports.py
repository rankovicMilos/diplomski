"""
Scraper for government market reports (DOCX/XLSX files).
Source: Serbian Ministry of Agriculture - https://www.minpolj.gov.rs/izvestaji-sa-trzista/

Downloads weekly market reports for agricultural commodities.
Files are organized by file type, year, and crop category.
"""
import os
import re
import logging
import urllib3
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

# Disable SSL warnings for this site (has certificate issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class MarketReportsScraper:
    """Scraper for government market reports (DOCX/XLSX files)."""

    # Storage path configuration
    SOURCE_CATEGORY = "market_reports"

    # Default years to scrape (can be overridden in event)
    DEFAULT_YEARS = [2024, 2025]

    def __init__(
        self,
        base_url: str = "",
        s3_bucket: str = ""
    ):
        """
        Initialize scraper.

        Args:
            base_url: URL to scrape
            s3_bucket: S3 bucket for uploads
        """
        self.base_url = base_url
        self.s3_bucket = s3_bucket

        # Use httpx with SSL verification disabled
        self.client = httpx.Client(verify=False, timeout=60.0, follow_redirects=True)

        import boto3
        self.s3_client = boto3.client("s3")

    def _s3_key_exists(self, s3_key: str) -> bool:
        """Check if an S3 key already exists."""
        if not self.s3_client or not self.s3_bucket:
            logger.debug(f"No S3 client/bucket configured")
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

    def scrape_section(
        self,
        section_key: str,
        section_name: str,
        years: Optional[list[int]] = None,
        limit: Optional[int] = None
    ) -> list[dict]:
        """
        Scrape files from a specific section.

        Args:
            section_key: Internal key (e.g., 'corn')
            section_name: Serbian name to search for (e.g., 'кукуруз')
            years: Filter by years in filename (e.g., [2024, 2025])
            limit: Max files to download (None = unlimited)

        Returns:
            List of downloaded file metadata
        """
        logger.info(f"Fetching page: {self.base_url}")
        response = self.client.get(self.base_url)
        response.raise_for_status()

        # Parse HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find download items for this section
        download_items = self._find_section_downloads(soup, section_name)

        if not download_items:
            logger.warning(f"No files found for section: {section_name}")
            return []

        logger.info(f"Found {len(download_items)} files in section '{section_name}'")

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

        # Download files (skip if already exists in S3)
        downloaded = []
        skipped = 0
        for item in download_items:
            file_url = item["url"]
            file_name = item["name"]

            # Extract year from filename for directory structure
            file_year = self._extract_year(file_name, years)
            clean_name = self._clean_filename(file_name)

            # Check if file already exists in S3 (for any known extension)
            for ext in [".docx", ".xlsx", ".doc", ".xls", ".pdf"]:
                file_type_dir = ext.lstrip(".").lower()
                if file_type_dir == "doc":
                    file_type_dir = "docx"
                elif file_type_dir == "xls":
                    file_type_dir = "xlsx"
                s3_key = f"{file_type_dir}/{self.SOURCE_CATEGORY}/{file_year}/{section_key}/{clean_name}{ext}"
                if self._s3_key_exists(s3_key):
                    logger.info(f"Skipping (exists): {clean_name}{ext}")
                    skipped += 1
                    break
            else:
                # File doesn't exist, download it
                logger.info(f"Downloading: {file_name}")
                result = self._download_file(
                    file_url=file_url,
                    section_key=section_key,
                    file_name=file_name,
                    file_year=file_year
                )
                if result:
                    downloaded.append(result)
                    logger.info(f"  Uploaded: {result.get('s3_key')}")

        logger.info(f"Section complete: {len(downloaded)} new, {skipped} skipped")
        return downloaded

    def _find_section_downloads(self, soup, section_name: str) -> list[dict]:
        """
        Find download items for a given section.

        Page structure:
        - Each file is in a <div class="well c2a3"> container
        - Inside: <h3 class="media-heading"><a>Title with year</a></h3>
        - And: <a class="wpdm-download-link" data-downloadurl="...">Преузми</a>
        """
        items = []
        section_name_lower = section_name.lower()

        # Find all file containers
        file_containers = soup.find_all("div", class_="well")

        for container in file_containers:
            # Find the h3 with title
            h3 = container.find("h3", class_="media-heading")
            if not h3:
                continue

            # Get title from the link inside h3
            title_link = h3.find("a")
            if not title_link:
                continue

            title_text = title_link.get_text(strip=True)

            # Check if this file belongs to our section
            if section_name_lower not in title_text.lower():
                continue

            # Find download button in same container
            download_btn = container.find("a", class_="wpdm-download-link")
            if not download_btn:
                continue

            data_url = download_btn.get("data-downloadurl", "")
            if not data_url:
                continue

            items.append({
                "url": data_url,
                "name": title_text,
            })
            logger.debug(f"Found file: {title_text}")

        return items

    def _filter_by_years(self, items: list[dict], years: list[int]) -> list[dict]:
        """Filter items that contain specified years in their name."""
        filtered = []
        year_patterns = [str(y) for y in years]

        for item in items:
            name = item.get("name", "")
            if any(year in name for year in year_patterns):
                filtered.append(item)
                logger.debug(f"Year match: {name}")

        return filtered

    def _extract_year(self, file_name: str, years: Optional[list[int]] = None) -> int:
        """Extract year from filename, defaulting to current year."""
        # Try to find a 4-digit year in the filename
        match = re.search(r'(20\d{2})', file_name)
        if match:
            return int(match.group(1))

        # If years filter provided, use the first one
        if years:
            return years[0]

        # Default to current year
        return datetime.now().year

    def _download_file(
        self,
        file_url: str,
        section_key: str,
        file_name: str,
        file_year: int
    ) -> Optional[dict]:
        """Download file and upload to S3."""
        try:
            response = self.client.get(file_url)
            response.raise_for_status()

            content = response.content

            # Determine file extension from magic bytes (actual content)
            extension = self._detect_extension_from_content(content)
            if not extension:
                # Fallback to content-type or URL
                extension = self._get_extension(file_url, response)

            # Clean filename for storage
            clean_name = self._clean_filename(file_name)

            # Determine file type directory (docx, xlsx, pdf, etc.)
            file_type_dir = extension.lstrip(".").lower()
            if file_type_dir in ["doc"]:
                file_type_dir = "docx"
            elif file_type_dir in ["xls"]:
                file_type_dir = "xlsx"

            return self._upload_to_s3(
                content=content,
                file_type_dir=file_type_dir,
                section_key=section_key,
                file_year=file_year,
                clean_name=clean_name,
                extension=extension,
                file_url=file_url,
                original_name=file_name
            )

        except Exception as e:
            logger.error(f"Failed to download {file_url}: {e}")
            return None

    def _upload_to_s3(
        self,
        content: bytes,
        file_type_dir: str,
        section_key: str,
        file_year: int,
        clean_name: str,
        extension: str,
        file_url: str,
        original_name: str
    ) -> dict:
        """
        Upload file to S3 with deterministic key (for deduplication).

        Structure: {file_type}/{source_category}/{year}/{crop}/{clean_name}{ext}
        Example: docx/market_reports/2024/corn/nedeljni_izvestaj_kukuruza_01_12_2024.docx
        """
        s3_key = (
            f"{file_type_dir}/{self.SOURCE_CATEGORY}/{file_year}/"
            f"{section_key}/{clean_name}{extension}"
        )

        # Truncate original_name to avoid exceeding Bedrock Knowledge Base
        # 2048 byte metadata limit (URL-encoded Cyrillic expands ~9x)
        truncated_name = original_name[:50] if len(original_name) > 50 else original_name

        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=s3_key,
            Body=content,
            Metadata={
                "source_url": file_url[:200],  # Truncate long URLs too
                "source_category": self.SOURCE_CATEGORY,
                "crop": section_key,
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
            "file_type": file_type_dir,
            "year": file_year,
            "crop": section_key,
            "size_bytes": len(content)
        }

    def _detect_extension_from_content(self, content: bytes) -> Optional[str]:
        """
        Detect file extension from magic bytes (file signature).

        Returns the actual file format regardless of what the server claims.
        """
        if len(content) < 8:
            return None

        # Check magic bytes
        # OLE Compound Document (old .doc, .xls, .ppt)
        ole_signature = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
        # ZIP-based formats (.docx, .xlsx, .pptx, etc.)
        zip_signature = b'PK\x03\x04'
        # PDF
        pdf_signature = b'%PDF'

        if content[:8] == ole_signature:
            # OLE format - need to determine if it's Word or Excel
            # Check for Word-specific markers in the content
            if b'Word.Document' in content or b'Microsoft Word' in content:
                return ".doc"
            elif b'Excel' in content or b'Workbook' in content:
                return ".xls"
            # Default to .doc for market reports (most common)
            return ".doc"

        elif content[:4] == zip_signature:
            # ZIP-based Office format - check internal structure
            # Look for specific content type markers
            if b'word/' in content or b'wordprocessingml' in content:
                return ".docx"
            elif b'xl/' in content or b'spreadsheetml' in content:
                return ".xlsx"
            elif b'ppt/' in content or b'presentationml' in content:
                return ".pptx"
            # Default to .docx for ZIP Office files
            return ".docx"

        elif content[:4] == pdf_signature:
            return ".pdf"

        return None

    def _get_extension(self, url: str, response: httpx.Response) -> str:
        """Get file extension from URL or content-type."""
        # Try from content-type header
        content_type = response.headers.get("content-type", "").lower()

        if "pdf" in content_type:
            return ".pdf"
        elif "spreadsheet" in content_type or "excel" in content_type:
            return ".xlsx"
        elif "word" in content_type or "msword" in content_type:
            return ".docx"
        elif "openxmlformats-officedocument.wordprocessingml" in content_type:
            return ".docx"
        elif "openxmlformats-officedocument.spreadsheetml" in content_type:
            return ".xlsx"

        # Try from content-disposition header
        content_disp = response.headers.get("content-disposition", "")
        if "filename=" in content_disp:
            match = re.search(r'filename[^;=\n]*=(["\']?)([^"\'\n;]+)\1', content_disp)
            if match:
                filename = match.group(2)
                ext = os.path.splitext(filename)[1]
                if ext:
                    return ext

        # Try from URL
        url_lower = url.lower()
        for ext in [".docx", ".xlsx", ".pdf", ".xls", ".doc"]:
            if ext in url_lower:
                return ext

        return ".docx"  # Default for market reports

    def _clean_filename(self, name: str) -> str:
        """Clean filename for storage."""
        # Remove invalid characters
        clean = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace spaces with underscores
        clean = clean.replace(' ', '_')
        # Remove extension if present (we'll add it back)
        clean = re.sub(r'\.(pdf|xlsx|xls|doc|docx)$', '', clean, flags=re.IGNORECASE)
        # Limit length
        return clean[:100]

    def close(self):
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
