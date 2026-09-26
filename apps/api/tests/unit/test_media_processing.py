"""Unit tests for EXIF strip and image variants."""

from __future__ import annotations

import io

from PIL import Image

from ent.jobs.tasks.media import process_clinical_image, sha256_hex


def _jpeg_bytes() -> bytes:
    image = Image.new("RGB", (64, 48), color=(12, 90, 180))
    buffer = io.BytesIO()
    # Embed EXIF via info dict where supported.
    image.save(buffer, format="JPEG", exif=image.getexif())
    return buffer.getvalue()


def test_process_clinical_image_builds_variants_and_checksum() -> None:
    raw = _jpeg_bytes()
    processed = process_clinical_image(raw, content_type="image/jpeg")
    cleaned = Image.open(io.BytesIO(processed.original_bytes))
    assert cleaned.size == (64, 48)
    assert processed.checksum_sha256 == sha256_hex(processed.original_bytes)
    assert processed.thumb_size[0] <= 256
    assert processed.preview_size[0] <= 1280
    assert len(processed.thumb_bytes) > 0
    assert len(processed.preview_bytes) > 0


def test_local_storage_roundtrip(tmp_path) -> None:
    import asyncio

    from ent.integrations.storage.local import LocalObjectStorage

    storage = LocalObjectStorage(tmp_path)
    key = "clinic/01ARZ3NDEKTSV4RRFFQ69G5FAV/patient/_none/logo/01ARZ3NDEKTSV4RRFFQ69G5FB1.png"

    async def _run() -> None:
        await storage.put_object_bytes(
            key=key, data=b"png-bytes", content_type="image/png"
        )
        assert await storage.object_exists(key=key)
        assert await storage.get_object_bytes(key=key) == b"png-bytes"
        upload = await storage.create_presigned_upload(
            key=key,
            content_type="image/png",
            expires_in_seconds=60,
        )
        assert upload.method == "PUT"
        assert "sig=" in upload.url

    asyncio.run(_run())
