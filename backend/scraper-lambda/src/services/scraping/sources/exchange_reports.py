"""
Scraper for commodity exchange weekly reports (Markdown files).
Source: NSComex - https://nscomex.com/podaci-iz-trgovanja/nedeljni-izvestaj/

Downloads weekly commodity trading reports and converts to markdown.
Files are organized by file type and year.
"""
import re
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)


class ExchangeReportsScraper:
    """Scraper for commodity exchange weekly reports (Markdown files)."""

    # Storage path configuration
    SOURCE_CATEGORY = "exchange_reports"

    def __init__(
        self,
        base_url: str = "https://nscomex.com/podaci-iz-trgovanja/nedeljni-izvestaj/",
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
            if error_code != '404':
                logger.warning(f"S3 head_object error for {s3_key}: {error_code} - {e}")
            return False

    def _get_s3_key(self, report: dict) -> str:
        """Generate deterministic S3 key for a report."""
        return f"markdown/{self.SOURCE_CATEGORY}/{report['year']}/report_{report['report_num']}.md"

    def scrape_reports(
        self,
        years: Optional[list[int]] = None,
        limit: Optional[int] = None,
        max_pages: int = 30
    ) -> list[dict]:
        """
        Scrape weekly reports.

        Args:
            years: Filter by years (e.g., [2024, 2025])
            limit: Max reports to download (None = unlimited)
            max_pages: Maximum pages to scan

        Returns:
            List of downloaded report metadata
        """
        if years is None:
            years = [2024, 2025]

        all_reports = []
        page = 1

        while page <= max_pages:
            if page == 1:
                url = self.base_url
            else:
                url = f"{self.base_url}page/{page}/"

            logger.info(f"Fetching page {page}: {url}")

            try:
                response = self.client.get(url)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.info(f"Page {page} not found, stopping pagination")
                    break
                raise

            reports = self._parse_page(response.text, years)

            # Log what we found on this page
            page_years = self._get_page_years(response.text)
            logger.info(f"Page {page}: found {len(reports)} matching reports, page years: {page_years}")

            all_reports.extend(reports)
            if reports:
                logger.info(f"Total collected: {len(all_reports)}")

            # Stop only when page has no reports from any of our target years
            if page_years and not any(y in years for y in page_years):
                logger.info(f"Page {page} has no target years {years}, only {page_years}. Stopping.")
                break

            # Also stop if page has no recognizable years at all (empty page)
            if not page_years:
                logger.info(f"Page {page} has no recognizable reports, stopping.")
                break

            # Apply limit
            if limit and len(all_reports) >= limit:
                all_reports = all_reports[:limit]
                break

            page += 1

        # Download all collected reports (skip if already exists in S3)
        downloaded = []
        skipped = 0
        for i, report in enumerate(all_reports):
            if limit and i >= limit:
                break

            # Check if report already exists in S3
            s3_key = self._get_s3_key(report)
            if self._s3_key_exists(s3_key):
                logger.info(f"Skipping (exists): report_{report['report_num']}.md")
                skipped += 1
                continue

            logger.info(f"Saving: {report['title']}")
            result = self._save_report(report)
            if result:
                downloaded.append(result)
                logger.info(f"  Saved: {result.get('s3_key')}")

        logger.info(f"Complete: {len(downloaded)} new, {skipped} skipped")
        return downloaded

    def _parse_page(self, html: str, years: list[int]) -> list[dict]:
        """Parse a page and extract reports matching the specified years."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        reports = []

        # Pattern: #46 (...2025) - extract report number and year
        title_pattern = re.compile(r'#(\d+)\s*\([^)]*\.?\s*(\d{4})\)')

        # Find all article elements (WordPress structure)
        articles = soup.find_all("article")

        for article in articles:
            header = article.find("header", class_="entry-header")
            if header:
                h2 = header.find("h2")
            else:
                h2 = article.find("h2")

            if not h2:
                continue

            title_text = h2.get_text(strip=True)
            match = title_pattern.search(title_text)

            if not match:
                continue

            report_num = match.group(1)
            year = int(match.group(2))

            # Extract dates from title
            dates = re.findall(r'(\d{1,2})\.\s*(\d{1,2})', title_text)
            if len(dates) >= 2:
                date_start = f"{dates[0][0]}.{dates[0][1]}"
                date_end = f"{dates[1][0]}.{dates[1][1]}"
            else:
                date_start = ""
                date_end = ""
                logger.warning(f"Could not extract dates from: {title_text}")

            # Filter by years
            if year not in years:
                continue

            # Extract content
            content_div = article.find("div", class_="entry-content")
            if content_div:
                content = content_div.get_text(separator="\n", strip=True)
                content = content.replace(title_text, "").strip()
                content = re.sub(r'^Nedeljni izveštaj\s*', '', content, flags=re.IGNORECASE)
            else:
                content = ""

            reports.append({
                "title": title_text,
                "report_num": report_num,
                "date_start": date_start,
                "date_end": date_end,
                "year": year,
                "content": content.strip()
            })

        # Deduplicate by report_num + year
        seen = {}
        for report in reports:
            key = (report["report_num"], report["year"])
            if key not in seen or len(report["content"]) > len(seen[key]["content"]):
                seen[key] = report

        return list(seen.values())

    def _get_page_years(self, html: str) -> list[int]:
        """Get all years mentioned in report titles on a page."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        years = set()

        title_pattern = re.compile(r'#\d+\s*\([^)]*\.?\s*(\d{4})\)')

        for h2 in soup.find_all("h2"):
            match = title_pattern.search(h2.get_text(strip=True))
            if match:
                years.add(int(match.group(1)))

        return list(years)

    def _save_report(self, report: dict) -> Optional[dict]:
        """Save report as markdown file to S3."""
        try:
            md_content = self._create_markdown(report)
            content_bytes = md_content.encode("utf-8")

            return self._upload_to_s3(
                content=content_bytes,
                report=report
            )

        except Exception as e:
            logger.error(f"Failed to save report {report['title']}: {e}")
            return None

    def _create_markdown(self, report: dict) -> str:
        """Create markdown content from report data."""
        lines = [
            f"# {report['title']}",
            "",
            f"**Source:** NSComex - Nedeljni izvestaj",
            f"**Report Number:** {report['report_num']}",
            f"**Period:** {report['date_start']} - {report['date_end']}.{report['year']}",
            f"**Year:** {report['year']}",
            "",
            "---",
            "",
            report["content"],
            "",
            "---",
            f"*Scraped from: https://nscomex.com/podaci-iz-trgovanja/nedeljni-izvestaj/*"
        ]
        return "\n".join(lines)

    def _upload_to_s3(
        self,
        content: bytes,
        report: dict
    ) -> dict:
        """
        Upload report to S3 with deterministic key (for deduplication).

        Structure: markdown/{source_category}/{year}/report_{num}.md
        Example: markdown/exchange_reports/2024/report_46.md
        """
        s3_key = self._get_s3_key(report)

        # Truncate title to avoid exceeding Bedrock Knowledge Base 2048 byte metadata limit
        truncated_title = report["title"][:50] if len(report["title"]) > 50 else report["title"]

        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=s3_key,
            Body=content,
            ContentType="text/markdown; charset=utf-8",
            Metadata={
                "source": "nscomex",
                "source_category": self.SOURCE_CATEGORY,
                "report_num": report["report_num"],
                "year": str(report["year"]),
                "title": quote(truncated_title, safe=""),
                "scraped_at": datetime.now(timezone.utc).isoformat()
            }
        )

        logger.info(f"Uploaded: s3://{self.s3_bucket}/{s3_key}")

        return {
            "s3_key": s3_key,
            "title": report["title"],
            "file_type": "markdown",
            "year": report["year"],
            "size_bytes": len(content)
        }

    def close(self):
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
