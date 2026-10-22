"""Base class for fetchers."""
import json
from abc import ABC, abstractmethod
from typing import Any, Optional

from ..exceptions import FetchError
from ..models import FetchedContent, FetchOptions


class BaseFetcher(ABC):
    """Retrieves a URL and returns its raw content."""

    def __init__(self, options: FetchOptions):
        self.options = options

    @abstractmethod
    def get(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        wait_for_selector: Optional[str] = None,
    ) -> FetchedContent:
        """
        Fetch a URL. Raises FetchError (or a subclass) on failure.

        wait_for_selector: for rendering fetchers, wait until this element exists before
        reading the page; overrides the source-wide fetch option. Plain HTTP ignores it.
        """

    def get_json(self, url: str, params: Optional[dict[str, Any]] = None) -> Any:
        response = self.get(url, params=params, headers={"Accept": "application/json"})
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            raise FetchError(f"Response is not valid JSON: {e}", url=url) from e

    def exists(self, url: str) -> bool:
        """Whether a URL resolves. Subclasses may override with a cheaper check."""
        try:
            self.get(url)
            return True
        except FetchError:
            return False

    def close(self) -> None:
        """Release resources."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
