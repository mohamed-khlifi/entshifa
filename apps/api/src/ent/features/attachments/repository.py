"""Attachment repository."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import selectinload

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, apply_pagination, normalize_pagination
from ent.core.schemas.base import PaginationParams
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

    async def public_ids_by_id(self, attachment_ids: set[int]) -> dict[int, str]:
        if not attachment_ids:
            return {}
        base = self._base_query().where(Attachment.id.in_(attachment_ids)).subquery()
        rows = (await self.session.execute(select(base.c.id, base.c.public_id))).all()
        return {int(row.id): str(row.public_id) for row in rows}

    async def list_for_patient(
        self, patient_id: int, *, limit: int = 500
    ) -> list[Attachment]:
        result = await self.session.scalars(
            self._base_query().where(Attachment.patient_id == patient_id).limit(limit),
        )
        return list(result.all())

    async def list_for_chart(
        self,
        *,
        patient_id: int,
        category: str | None,
        laterality: str | None,
        captured_from: datetime | None,
        captured_to: datetime | None,
        page: PaginationParams | None,
    ) -> Page[Attachment]:
        """Tenant-scoped chart media, newest capture (or upload) first."""

        resolved = normalize_pagination(page)
        stamp = func.coalesce(Attachment.captured_at, Attachment.created_at)
        stmt = self._base_query().where(Attachment.patient_id == patient_id)
        if category is not None:
            stmt = stmt.where(Attachment.category == category)
        if laterality is not None:
            stmt = stmt.where(Attachment.laterality == laterality)
        if captured_from is not None:
            stmt = stmt.where(stamp >= captured_from)
        if captured_to is not None:
            stmt = stmt.where(stamp < captured_to)
        total = (
            await self.session.execute(
                select(func.count()).select_from(stmt.subquery()),
            )
        ).scalar_one()
        stmt = stmt.options(selectinload(Attachment.variants)).order_by(
            desc(stamp), desc(Attachment.id)
        )
        rows = list(
            (await self.session.scalars(apply_pagination(stmt, resolved))).all()
        )
        return Page(
            items=rows,
            total=int(total or 0),
            limit=resolved.limit,
            offset=resolved.offset,
            next_cursor=None,
        )

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
