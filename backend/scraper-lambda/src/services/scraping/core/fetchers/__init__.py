"""Fetchers. Importing this package registers all fetcher classes with FetcherFactory."""
from .base import BaseFetcher
from .browser_fetcher import BrowserFetcher
from .factory import FetcherFactory
from .http_fetcher import HttpFetcher

__all__ = ["BaseFetcher", "BrowserFetcher", "FetcherFactory", "HttpFetcher"]
