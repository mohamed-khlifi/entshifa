"""Object storage port (architecture §34)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class PresignedUrl:
    url: str
    method: str
    expires_in_seconds: int
    headers: dict[str, str]


@runtime_checkable
class ObjectStorage(Protocol):
    """Storage adapter: clients upload/download via pre-signed URLs only."""

    async def ping(self) -> None:
        """Raise if the backend is unreachable."""

    async def create_presigned_upload(
        self,
        *,
        key: str,
        content_type: str,
        expires_in_seconds: int,
    ) -> PresignedUrl:
        """Short-lived PUT URL; large files never pass through the API process."""

    async def create_presigned_download(
        self,
        *,
        key: str,
        expires_in_seconds: int,
        filename: str | None = None,
    ) -> PresignedUrl:
        """Short-lived GET URL after permission checks."""

    async def object_exists(self, *, key: str) -> bool: ...

    async def get_object_bytes(self, *, key: str) -> bytes:
        """Server-side read for worker processing (not an HTTP response path)."""

    async def put_object_bytes(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str,
    ) -> None:
        """Server-side write for processed variants."""

    async def delete_object(self, *, key: str) -> None: ...
