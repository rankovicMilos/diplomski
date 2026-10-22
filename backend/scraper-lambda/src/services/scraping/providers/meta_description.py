"""
Live provider for pages that state the current value in their description.

Trading Economics, for example, publishes:
  "Steel fell to 3,102 CNY/T on September 23, 2026, down 0.16% from the previous day. ..."
The chart history is loaded by JavaScript from a paid API, so only the current value is
available. Running the source daily builds our own history in history.csv.
"""
import re

from bs4 import BeautifulSoup

from ..core.exceptions import FetchError
from ..core.models import DataTable, LiveSnapshot
from .base import BaseLiveProvider
from .factory import ProviderFactory
from .html_table import _meta
from .timestamps import find_source_timestamp, normalize

# "rose to 3,102 CNY/T on ...", "traded flat at 4,962 CNY/T on ..."
VALUE_PATTERN = re.compile(
    r"\b(?:to|at) (?P<value>[\d,]+(?:\.\d+)?) (?P<unit>[A-Za-z$€%/]+(?:/[A-Za-z]+)?)"
    r" on (?P<date>[A-Z][a-z]+ \d{1,2}, \d{4})"
)
# Clauses with a percentage: "down 0.16% from the previous day", "has risen 1.60%",
# "is still 0.44% lower than a year ago"
CHANGE_PATTERN = re.compile(r"[^.,]*\d+(?:\.\d+)?%[^.,]*")


@ProviderFactory.register("meta_description")
class MetaDescriptionProvider(BaseLiveProvider):
    """
    params:
      instrument:        name of the instrument in the output (default: page title)
      extra_selector:    CSS selector of additional text to include (optional)
      timestamp_selector / timestamp_pattern / source_timezone:
                         where to read the quote time (see providers/timestamps.py);
                         falls back to the date in the description
    """

    def snapshot(self, url: str) -> LiveSnapshot:
        page = self.fetcher.get(url)
        soup = BeautifulSoup(page.text, "lxml")
        description = _meta(soup, "description") or _meta(soup, "og:description")
        if not description:
            raise FetchError("Page has no meta description", url=url)

        title = self.params.get("instrument") or (soup.title.get_text(strip=True) if soup.title else url)
        summary = description
        if self.params.get("extra_selector"):
            extra = soup.select_one(self.params["extra_selector"])
            if extra:
                summary += "\n\n" + extra.get_text(" ", strip=True)

        source_timestamp, origin = find_source_timestamp(soup, self.params)

        tables = []
        match = VALUE_PATTERN.search(description)
        if match:
            quote_date = normalize(match["date"])
            if not source_timestamp:
                source_timestamp, origin = quote_date, "meta description"
            changes = "; ".join(m.group(0).strip() for m in CHANGE_PATTERN.finditer(description))
            tables.append(DataTable(
                title="Current value",
                columns=["Instrument", "Quote date", "Value", "Unit", "Changes"],
                rows=[[title, quote_date, match["value"].replace(",", ""), match["unit"], changes]],
                source_url=url,
            ))
        return LiveSnapshot(title=title, summary=summary, tables=tables,
                            source_timestamp=source_timestamp, source_timestamp_origin=origin)
