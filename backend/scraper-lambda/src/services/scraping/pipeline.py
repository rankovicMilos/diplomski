"""
Scraping pipeline orchestration.

Coordinates scraping from multiple sources:
- Market Reports: Government market reports (DOCX/XLSX)
- Exchange Reports: Commodity exchange weekly reports (Markdown)
- Statistics: Government statistical tables (CSV)
- Zita Srbije: Serbian Grain Association monthly reports (PDF)
- Eurostat: Eurostat regional yearbook (PDF)

Storage Structure (S3):
├── docx/
│   └── market_reports/{year}/{crop}/
├── xlsx/
│   └── market_reports/{year}/{crop}/
├── markdown/
│   ├── exchange_reports/{year}/
│   └── statistics/tables/
├── csv/
│   └── statistics/tables/
└── pdf/
    ├── zitasrbije_reports/{year}/
    └── eurostat_reports/{year}/
"""
import os
import logging
from typing import Optional

from .sources.market_reports import MarketReportsScraper
from .sources.exchange_reports import ExchangeReportsScraper
from .sources.statistics import StatisticsScraper
from .sources.zitasrbije_reports import ZitaSrbijeScraper
from .sources.eurostat_reports import EurostatScraper
from .core.period import analysis_years

logger = logging.getLogger(__name__)

# Section configurations for market reports
# Key: internal name, Value: Serbian search term (Cyrillic)
SECTIONS = {
    "corn": "кукуруз",        # matches "кукуруза"
    "wheat": "пшениц",        # matches "пшенице"
    "sunflower": "сунцокрет", # matches "сунцокрета"
    "soybean": "сој",         # matches "соје"
}

# Default URLs
MARKET_REPORTS_URL = "https://www.minpolj.gov.rs/izvestaji-sa-trzista/"
EXCHANGE_REPORTS_URL = "https://nscomex.com/podaci-iz-trgovanja/nedeljni-izvestaj/"
ZITASRBIJE_URL = "https://www.zitasrbije.rs/tekst.php?grupaA=13"
EUROSTAT_URL = "https://ec.europa.eu/eurostat/web/main/publications/flagship-publications"


# ============================================================================
# Market Reports Scraper (DOCX/XLSX files from government)
# ============================================================================

def run_market_reports_scraping(
    sections: Optional[list[str]] = None,
    years: Optional[list[int]] = None,
    limit: Optional[int] = None
) -> dict:
    """
    Scrape government market reports (DOCX/XLSX files).

    Args:
        sections: List of sections to scrape (corn, wheat, sunflower, soybean).
                  If None, scrapes all.
        years: Filter by years (default: the last two completed years)
        limit: Max files per section (None = unlimited)

    Returns:
        dict with results per section
    """
    if years is None:
        years = analysis_years()

    base_url = os.environ.get("MARKET_REPORTS_URL", MARKET_REPORTS_URL)
    s3_bucket = os.environ.get("RAW_DATA_BUCKET")
    if not s3_bucket:
        raise ValueError("RAW_DATA_BUCKET environment variable not set")

    target_sections = sections or list(SECTIONS.keys())

    with MarketReportsScraper(
        base_url=base_url,
        s3_bucket=s3_bucket
    ) as scraper:
        results = {}

        for section in target_sections:
            if section not in SECTIONS:
                logger.warning(f"Unknown section: {section}, skipping")
                continue

            section_name = SECTIONS[section]
            logger.info(f"Scraping section: {section} ({section_name})")

            try:
                result = scraper.scrape_section(
                    section_key=section,
                    section_name=section_name,
                    years=years,
                    limit=limit
                )
                results[section] = {"status": "success", "files": result, "count": len(result)}
            except Exception as e:
                logger.error(f"Failed to scrape {section}: {e}")
                results[section] = {"status": "error", "error": str(e)}

    return results


# ============================================================================
# Exchange Reports Scraper (Markdown files from commodity exchange)
# ============================================================================

def run_exchange_reports_scraping(
    years: Optional[list[int]] = None,
    limit: Optional[int] = None
) -> dict:
    """
    Scrape commodity exchange weekly reports.

    Args:
        years: Filter by years (default: the last two completed years)
        limit: Max reports to download (None = unlimited)

    Returns:
        dict with results
    """
    if years is None:
        years = analysis_years()

    s3_bucket = os.environ.get("RAW_DATA_BUCKET")
    if not s3_bucket:
        raise ValueError("RAW_DATA_BUCKET environment variable not set")

    with ExchangeReportsScraper(
        base_url=EXCHANGE_REPORTS_URL,
        s3_bucket=s3_bucket
    ) as scraper:
        try:
            result = scraper.scrape_reports(
                years=years,
                limit=limit
            )
            return {"exchange_reports": {"status": "success", "files": result, "count": len(result)}}
        except Exception as e:
            logger.error(f"Failed to scrape exchange reports: {e}")
            return {"exchange_reports": {"status": "error", "error": str(e)}}


# ============================================================================
# Statistics Scraper (CSV files from government statistics)
# ============================================================================

def run_statistics_scraping(
    result_url: str,
    years: Optional[list[int]] = None,
    products: Optional[list[str]] = None
) -> dict:
    """
    Scrape government statistical tables.

    Args:
        result_url: The stat.gov.rs Result URL or dataset ID
        years: Years to filter (default: the last two completed years)
        products: Optional list of products to filter

    Returns:
        dict with results
    """
    if years is None:
        years = analysis_years()

    s3_bucket = os.environ.get("RAW_DATA_BUCKET")
    if not s3_bucket:
        raise ValueError("RAW_DATA_BUCKET environment variable not set")

    with StatisticsScraper(s3_bucket=s3_bucket) as scraper:
        try:
            result = scraper.scrape_crop_statistics(
                result_url=result_url,
                years=years,
                products=products
            )
            if result:
                return {"statistics": {"status": "success", "files": [result], "count": 1}}
            else:
                return {"statistics": {"status": "error", "error": "No data scraped"}}
        except Exception as e:
            logger.error(f"Failed to scrape statistics: {e}")
            return {"statistics": {"status": "error", "error": str(e)}}


# ============================================================================
# Zita Srbije Reports Scraper (PDF files from grain association)
# ============================================================================

def run_zitasrbije_scraping(
    years: Optional[list[int]] = None,
    limit: Optional[int] = None
) -> dict:
    """
    Scrape Zita Srbije monthly PDF reports.

    Args:
        years: Filter by years (default: the last two completed years)
        limit: Max reports to download (None = unlimited)

    Returns:
        dict with results
    """
    if years is None:
        years = analysis_years()

    s3_bucket = os.environ.get("RAW_DATA_BUCKET")
    if not s3_bucket:
        raise ValueError("RAW_DATA_BUCKET environment variable not set")

    with ZitaSrbijeScraper(s3_bucket=s3_bucket) as scraper:
        try:
            result = scraper.scrape_reports(
                years=years,
                limit=limit
            )
            return {"zitasrbije": {"status": "success", "files": result, "count": len(result)}}
        except Exception as e:
            logger.error(f"Failed to scrape Zita Srbije reports: {e}")
            return {"zitasrbije": {"status": "error", "error": str(e)}}


# ============================================================================
# Eurostat Reports Scraper (PDF files from Eurostat)
# ============================================================================

def run_eurostat_scraping(
    years: Optional[list[int]] = None,
    limit: Optional[int] = None
) -> dict:
    """
    Scrape Eurostat regional yearbook PDFs.

    Args:
        years: Filter by years (default: the last two completed years)
        limit: Max reports to download (None = unlimited)

    Returns:
        dict with results
    """
    if years is None:
        years = analysis_years()

    s3_bucket = os.environ.get("RAW_DATA_BUCKET")
    if not s3_bucket:
        raise ValueError("RAW_DATA_BUCKET environment variable not set")

    with EurostatScraper(s3_bucket=s3_bucket) as scraper:
        try:
            result = scraper.scrape_reports(
                years=years,
                limit=limit
            )
            return {"eurostat": {"status": "success", "files": result, "count": len(result)}}
        except Exception as e:
            logger.error(f"Failed to scrape Eurostat reports: {e}")
            return {"eurostat": {"status": "error", "error": str(e)}}


# ============================================================================
# Combined Scraping (All Sources)
# ============================================================================

def run_all_scrapers(
    years: Optional[list[int]] = None,
    limit: Optional[int] = None,
    statistics_url: Optional[str] = None
) -> dict:
    """
    Run all scrapers.

    Args:
        years: Filter by years (default: the last two completed years)
        limit: Max files per source (None = unlimited)
        statistics_url: URL for statistics scraper (optional)

    Returns:
        dict with results from all scrapers
    """
    if years is None:
        years = analysis_years()

    results = {}

    # Market Reports
    logger.info("=" * 60)
    logger.info("Starting Market Reports scraper...")
    results["market_reports"] = run_market_reports_scraping(
        years=years,
        limit=limit
    )

    # Exchange Reports
    logger.info("=" * 60)
    logger.info("Starting Exchange Reports scraper...")
    results["exchange_reports"] = run_exchange_reports_scraping(
        years=years,
        limit=limit
    )

    # Statistics (if URL provided)
    if statistics_url:
        logger.info("=" * 60)
        logger.info("Starting Statistics scraper...")
        results["statistics"] = run_statistics_scraping(
            result_url=statistics_url,
            years=years
        )

    # Zita Srbije Reports
    logger.info("=" * 60)
    logger.info("Starting Zita Srbije scraper...")
    results["zitasrbije"] = run_zitasrbije_scraping(
        years=years,
        limit=limit
    )

    # Eurostat Reports
    logger.info("=" * 60)
    logger.info("Starting Eurostat scraper...")
    results["eurostat"] = run_eurostat_scraping(
        years=years,
        limit=limit
    )

    return results


# ============================================================================
# Legacy aliases (for backwards compatibility)
# ============================================================================

run_scraping = run_market_reports_scraping
run_nscomex_scraping = run_exchange_reports_scraping
run_statgov_scraping = run_statistics_scraping
