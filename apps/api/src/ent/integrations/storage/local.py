"""Local filesystem storage adapter for unit tests (no MinIO required)."""

from __future__ import annotations

import hashlib
import hmac
import time
from pathlib import Path
from urllib.parse import urlencode

from ent.integrations.storage.port import PresignedUrl


class LocalObjectStorage:
    """
    Stores objects under a root directory.

    Presigned URLs are HMAC-signed file:// tokens consumed only by tests via
    ``consume_presigned_put`` / ``consume_presigned_get``. Production uses S3.
    """

    def __init__(
        self, root: Path, *, signing_secret: str = "local-dev-storage"
    ) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)
        self._secret = signing_secret.encode("utf-8")

    def _path_for(self, key: str) -> Path:
        path = (self._root / key).resolve()
        if not str(path).startswith(str(self._root.resolve())):
            msg = "invalid storage key path"
            raise ValueError(msg)
        return path

    async def ping(self) -> None:
        if not self._root.exists():
            msg = f"local storage root missing: {self._root}"
            raise FileNotFoundError(msg)

    def _sign(self, *, key: str, method: str, expires_at: int) -> str:
        payload = f"{method}:{key}:{expires_at}".encode()
        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()

    async def create_presigned_upload(
        self,
        *,
        key: str,
        content_type: str,
        expires_in_seconds: int,
    ) -> PresignedUrl:
        expires_at = int(time.time()) + expires_in_seconds
        sig = self._sign(key=key, method="PUT", expires_at=expires_at)
        query = urlencode(
            {
                "key": key,
                "expires": str(expires_at),
                "sig": sig,
                "contentType": content_type,
            },
        )
        return PresignedUrl(
            url=f"local-storage://upload?{query}",
            method="PUT",
            expires_in_seconds=expires_in_seconds,
            headers={"Content-Type": content_type},
        )

    async def create_presigned_download(
        self,
        *,
        key: str,
        expires_in_seconds: int,
        filename: str | None = None,
    ) -> PresignedUrl:
        expires_at = int(time.time()) + expires_in_seconds
        sig = self._sign(key=key, method="GET", expires_at=expires_at)
        params = {"key": key, "expires": str(expires_at), "sig": sig}
        if filename:
            params["filename"] = filename
        return PresignedUrl(
            url=f"local-storage://download?{urlencode(params)}",
            method="GET",
            expires_in_seconds=expires_in_seconds,
            headers={},
        )

    def verify_presigned(
        self,
        *,
        key: str,
        method: str,
        expires: int,
        sig: str,
    ) -> bool:
        if int(time.time()) > expires:
            return False
        expected = self._sign(key=key, method=method, expires_at=expires)
        return hmac.compare_digest(expected, sig)

    async def object_exists(self, *, key: str) -> bool:
        return self._path_for(key).is_file()

    async def get_object_bytes(self, *, key: str) -> bytes:
        path = self._path_for(key)
        return path.read_bytes()

    async def put_object_bytes(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str,
    ) -> None:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        # content_type retained only for API symmetry; filesystem has no metadata store.
        _ = content_type

    async def delete_object(self, *, key: str) -> None:
        path = self._path_for(key)
        if path.is_file():
            path.unlink()

    async def consume_presigned_put(
        self,
        *,
        key: str,
        expires: int,
        sig: str,
        data: bytes,
        content_type: str,
    ) -> None:
        if not self.verify_presigned(key=key, method="PUT", expires=expires, sig=sig):
            msg = "invalid or expired local upload URL"
            raise PermissionError(msg)
        await self.put_object_bytes(key=key, data=data, content_type=content_type)
