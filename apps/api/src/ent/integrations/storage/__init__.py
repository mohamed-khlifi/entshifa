"""Storage factory and health helpers."""

from __future__ import annotations

from pathlib import Path

from ent.integrations.storage.local import LocalObjectStorage
from ent.integrations.storage.port import ObjectStorage
from ent.integrations.storage.s3 import S3ObjectStorage, ping_storage
from ent.settings import Settings

__all__ = [
    "LocalObjectStorage",
    "ObjectStorage",
    "S3ObjectStorage",
    "get_object_storage",
    "ping_storage",
]


def get_object_storage(settings: Settings) -> ObjectStorage:
    """
    Return the configured storage adapter.

    Production and local Docker use S3/MinIO. Set STORAGE_BACKEND=local for
    filesystem-backed unit tests without MinIO.
    """

    if settings.storage_backend == "local":
        return LocalObjectStorage(Path(settings.local_storage_root))
    return S3ObjectStorage(settings)
