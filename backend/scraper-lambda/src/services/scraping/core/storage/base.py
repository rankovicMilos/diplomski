"""Base class for storage backends."""
import json
from abc import ABC, abstractmethod
from typing import Any, Optional

from ..models import StoredDocument

METADATA_SUFFIX = ".metadata.json"

# Fields written to the Knowledge Base sidecar. S3 Vectors allows at most 2048 bytes of
# filterable metadata per chunk, including what Bedrock adds itself (source URI, chunk id),
# so only short fields used for filtering go there. The object's own S3 metadata keeps all.
KB_METADATA_KEYS = ("source_id", "industry", "industries", "sections", "year", "period")


class BaseStorage(ABC):
    """
    Stores scraped documents under deterministic keys.

    Keys are given as a *stem* (no extension), because the extension is only known after
    the document is fetched. Each document is written together with a Bedrock Knowledge
    Base metadata sidecar: `<key>.metadata.json` with `metadataAttributes` (KB_METADATA_KEYS),
    which lets the report generator filter retrieval by industry and section.
    """

    @abstractmethod
    def find(self, stem: str) -> Optional[str]:
        """Return the key of an existing document with this stem, or None."""

    @abstractmethod
    def read(self, key: str) -> Optional[bytes]:
        """Return the stored bytes, or None if the key does not exist."""

    @abstractmethod
    def _write(self, key: str, content: bytes, content_type: str, metadata: dict[str, Any]) -> str:
        """Write bytes to a key. Returns a human-readable location (path or s3:// URI)."""

    def exists(self, stem: str) -> bool:
        return self.find(stem) is not None

    def save(self, stem: str, document: StoredDocument, metadata: dict[str, Any]) -> str:
        key = f"{stem}{document.extension}"
        location = self._write(key, document.content, document.content_type, metadata)
        kb_metadata = {k: metadata[k] for k in KB_METADATA_KEYS if k in metadata}
        sidecar = json.dumps({"metadataAttributes": kb_metadata}, ensure_ascii=False, indent=2)
        self._write(key + METADATA_SUFFIX, sidecar.encode("utf-8"), "application/json", {})
        return location
