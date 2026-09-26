"""Background job: process an uploaded attachment (architecture §34)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select

from ent.core.db.session import get_session_factory
from ent.features.attachments.models import IMAGE_CATEGORIES, Attachment, MediaVariant
from ent.integrations.storage import get_object_storage
from ent.integrations.storage.keys import variant_storage_key
from ent.integrations.storage.malware import scan_bytes
from ent.jobs.base import register_job
from ent.jobs.tasks.media import (
    is_processable_image,
    process_clinical_image,
    sha256_hex,
)
from ent.settings import get_settings

JOB_PROCESS_ATTACHMENT = "jobs.process_attachment"


@register_job(JOB_PROCESS_ATTACHMENT, max_attempts=5)
async def process_attachment(
    *, attachment_public_id: str, **_extra: Any
) -> dict[str, Any]:
    """
    Strip EXIF, scan malware, compute checksum, write thumb/preview variants.

    Runs in the worker; object bytes never transit the API request path.
    """

    settings = get_settings()
    storage = get_object_storage(settings)
    factory = get_session_factory()

    async with factory() as session:
        result = await session.execute(
            select(Attachment).where(
                Attachment.public_id == attachment_public_id,
                Attachment.deleted_at.is_(None),
            ),
        )
        attachment = result.scalar_one_or_none()
        if attachment is None:
            return {"ok": False, "reason": "not_found"}

        attachment.processing_status = "processing"
        await session.commit()

        clinic_id = int(attachment.clinic_id)
        attachment_id = int(attachment.id)
        storage_key = attachment.storage_key
        content_type = attachment.content_type
        category = attachment.category
        filename = attachment.filename

    data = await storage.get_object_bytes(key=storage_key)
    scan = scan_bytes(data=data, content_type=content_type, filename=filename)
    if not scan.clean:
        async with factory() as session:
            row = await session.get(Attachment, attachment_id)
            assert row is not None
            row.processing_status = "failed"
            await session.commit()
        return {"ok": False, "reason": "malware", "detail": scan.detail}

    width: int | None = None
    height: int | None = None
    checksum = sha256_hex(data)
    variants_written: list[str] = []
    exif_stripped = False

    if category in IMAGE_CATEGORIES and is_processable_image(content_type):
        processed = process_clinical_image(data, content_type=content_type)
        exif_stripped = processed.exif_stripped
        checksum = processed.checksum_sha256
        width, height = processed.width, processed.height
        # Overwrite original with EXIF-stripped bytes.
        await storage.put_object_bytes(
            key=storage_key,
            data=processed.original_bytes,
            content_type=processed.content_type,
        )
        content_type = processed.content_type

        for variant_name, payload, size in (
            ("thumb", processed.thumb_bytes, processed.thumb_size),
            ("preview", processed.preview_bytes, processed.preview_size),
        ):
            vkey = variant_storage_key(storage_key, variant=variant_name)
            await storage.put_object_bytes(
                key=vkey,
                data=payload,
                content_type="image/jpeg",
            )
            variants_written.append(variant_name)
            async with factory() as session:
                existing = await session.execute(
                    select(MediaVariant).where(
                        MediaVariant.attachment_id == attachment_id,
                        MediaVariant.variant == variant_name,
                        MediaVariant.deleted_at.is_(None),
                    ),
                )
                variant_row: MediaVariant | None = existing.scalar_one_or_none()
                if variant_row is None:
                    session.add(
                        MediaVariant(
                            clinic_id=clinic_id,
                            attachment_id=attachment_id,
                            variant=variant_name,
                            storage_key=vkey,
                            width=size[0],
                            height=size[1],
                            size_bytes=len(payload),
                            content_type="image/jpeg",
                        ),
                    )
                else:
                    variant_row.storage_key = vkey
                    variant_row.width = size[0]
                    variant_row.height = size[1]
                    variant_row.size_bytes = len(payload)
                    variant_row.content_type = "image/jpeg"
                await session.commit()

    async with factory() as session:
        row = await session.get(Attachment, attachment_id)
        assert row is not None
        row.checksum_sha256 = checksum
        row.width = width
        row.height = height
        row.content_type = content_type
        row.size_bytes = len(await storage.get_object_bytes(key=storage_key))
        row.virus_scanned_at = scan.scanned_at
        row.processing_status = "ready"
        await session.commit()

    return {
        "ok": True,
        "attachment_public_id": attachment_public_id,
        "exif_stripped": exif_stripped,
        "variants": variants_written,
        "checksum_sha256": checksum,
        "malware_engine": scan.engine,
    }
