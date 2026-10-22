"""Local filesystem storage, for testing scrapers without AWS."""
from pathlib import Path
from typing import Any, Optional

from .base import METADATA_SUFFIX, BaseStorage
from .factory import StorageFactory


@StorageFactory.register("local")
class LocalStorage(BaseStorage):
    """Writes documents under a local directory, mirroring the S3 key layout."""

    def __init__(self, base_dir: str = "output"):
        self.base_dir = Path(base_dir).resolve()

    def find(self, stem: str) -> Optional[str]:
        path = self.base_dir / stem
        if not path.parent.exists():
            return None
        for candidate in path.parent.glob(f"{path.name}.*"):
            if not candidate.name.endswith(METADATA_SUFFIX):
                return candidate.relative_to(self.base_dir).as_posix()
        return None

    def read(self, key: str) -> Optional[bytes]:
        path = self.base_dir / key
        return path.read_bytes() if path.exists() else None

    def _write(self, key: str, content: bytes, content_type: str, metadata: dict[str, Any]) -> str:
        path = self.base_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)
