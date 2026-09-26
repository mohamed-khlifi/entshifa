"""Attachment repository."""

from __future__ import annotations

from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.features.attachments.models import Attachment, MediaVariant


class AttachmentRepository(BaseRepository[Attachment]):
    model = Attachment

    async def get_by_public_id_with_variants(self, public_id: str) -> Attachment | None:
        stmt = (
            self._base_query()
            .where(Attachment.public_id == public_id)
            .options(selectinload(Attachment.variants))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_storage_key(self, storage_key: str) -> Attachment | None:
        result = await self.session.execute(
            self._base_query().where(Attachment.storage_key == storage_key),
        )
        return result.scalar_one_or_none()


class MediaVariantRepository(BaseRepository[MediaVariant]):
    model = MediaVariant

    async def get_for_attachment_variant(
        self,
        *,
        attachment_id: int,
        variant: str,
    ) -> MediaVariant | None:
        result = await self.session.execute(
            self._base_query().where(
                MediaVariant.attachment_id == attachment_id,
                MediaVariant.variant == variant,
            ),
        )
        return result.scalar_one_or_none()

    async def list_for_attachment(self, attachment_id: int) -> list[MediaVariant]:
        result = await self.session.execute(
            self._base_query()
            .where(MediaVariant.attachment_id == attachment_id)
            .order_by(MediaVariant.variant),
        )
        return list(result.scalars().all())
