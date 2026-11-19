"""Evidence file storage. Originals are write-once; derived files go in a separate area.

Local-disk implementation for the MVP. Swap `LocalStorage` for an R2 client in Phase 2
without changing callers.
"""
import hashlib
from pathlib import Path

from ..config import STORAGE_DIR


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class LocalStorage:
    def __init__(self, root: Path = STORAGE_DIR):
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root.resolve() not in path.parents:
            raise ValueError("invalid storage key")
        return path

    def put_original(self, data: bytes, extension: str) -> tuple[str, str]:
        """Store bytes under their content hash. Never overwrites. Returns (key, sha256)."""
        digest = sha256_hex(data)
        key = f"originals/{digest[:2]}/{digest}{extension}"
        path = self._path(key)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return key, digest

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def verify(self, key: str, expected_hash: str) -> bool:
        """Storage integrity check (PRD §16.5)."""
        return self.exists(key) and sha256_hex(self.read(key)) == expected_hash


storage = LocalStorage()
