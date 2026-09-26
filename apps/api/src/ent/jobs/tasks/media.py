"""Image processing: EXIF strip, checksum, thumbnail/preview variants."""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

from PIL import Image, ImageOps


@dataclass(frozen=True, slots=True)
class ProcessedImage:
    """Original bytes with EXIF/GPS removed, plus derived variants."""

    original_bytes: bytes
    content_type: str
    width: int
    height: int
    checksum_sha256: str
    thumb_bytes: bytes
    preview_bytes: bytes
    thumb_size: tuple[int, int]
    preview_size: tuple[int, int]
    exif_stripped: bool


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _save_jpeg(image: Image.Image, *, quality: int) -> bytes:
    buffer = io.BytesIO()
    rgb = image.convert("RGB")
    rgb.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()


def process_clinical_image(data: bytes, *, content_type: str) -> ProcessedImage:
    """
    Strip EXIF (including GPS), re-encode, and build thumb/preview JPEGs.

    Location metadata in a clinical photo is a privacy problem (architecture §34).
    """

    with Image.open(io.BytesIO(data)) as raw:
        # Apply orientation then drop all EXIF for the cleaned original.
        oriented = ImageOps.exif_transpose(raw)
        assert oriented is not None
        width, height = oriented.size
        had_exif = bool(raw.getexif()) or bool(getattr(raw, "info", {}).get("exif"))
        cleaned = _save_jpeg(oriented, quality=92)

        thumb = oriented.copy()
        thumb.thumbnail((256, 256))
        thumb_bytes = _save_jpeg(thumb, quality=80)

        preview = oriented.copy()
        preview.thumbnail((1280, 1280))
        preview_bytes = _save_jpeg(preview, quality=85)

    return ProcessedImage(
        original_bytes=cleaned,
        content_type="image/jpeg",
        width=width,
        height=height,
        checksum_sha256=sha256_hex(cleaned),
        thumb_bytes=thumb_bytes,
        preview_bytes=preview_bytes,
        thumb_size=thumb.size,
        preview_size=preview.size,
        exif_stripped=had_exif or content_type.startswith("image/"),
    )


def is_processable_image(content_type: str) -> bool:
    return content_type.lower() in {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/tiff",
    }
