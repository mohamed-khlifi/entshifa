"""Tenant-scoped document persistence."""

from __future__ import annotations

from sqlalchemy import Select, and_, desc, false, func, or_, select

from ent.core.repository.base import BaseRepository
from ent.core.repository.pagination import Page, apply_pagination, normalize_pagination
from ent.core.schemas.base import PaginationParams
from ent.features.documents.models import (
    Document,
    DocumentRecipient,
    DocumentTemplate,
    DocumentTemplateVersion,
)


class DocumentTemplateRepository(BaseRepository[DocumentTemplate]):
    """System templates (clinic_id null) plus the caller's clinic templates."""

    model = DocumentTemplate

    def _base_query(self) -> Select[tuple[DocumentTemplate]]:
        stmt = select(self.model).where(self.model.deleted_at.is_(None))
        if self.clinic_id is None:
            return stmt.where(false())
        return stmt.where(
            or_(
                self.model.clinic_id == self.clinic_id,
                and_(
                    self.model.clinic_id.is_(None),
                    self.model.is_system.is_(True),
                ),
            )
        )

    async def get_by_code(self, code: str) -> DocumentTemplate | None:
        """Clinic override wins over the system template with the same code."""

        result = await self.session.execute(
            self._base_query()
            .where(
                self.model.code == code,
                self.model.is_active.is_(True),
            )
            .order_by(self.model.clinic_id.is_(None))
        )
        return result.scalars().first()

    async def get_system_by_code(self, code: str) -> DocumentTemplate | None:
        result = await self.session.execute(
            select(self.model).where(
                self.model.deleted_at.is_(None),
                self.model.clinic_id.is_(None),
                self.model.is_system.is_(True),
                self.model.code == code,
            )
        )
        return result.scalar_one_or_none()

    async def list_active(
        self, *, page: PaginationParams | None
    ) -> Page[DocumentTemplate]:
        resolved = normalize_pagination(page)
        stmt = self._base_query().where(self.model.is_active.is_(True))
        total = (
            await self.session.execute(
                select(func.count()).select_from(stmt.subquery())
            )
        ).scalar_one()
        stmt = stmt.order_by(self.model.code)
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


class DocumentTemplateVersionRepository(BaseRepository[DocumentTemplateVersion]):
    model = DocumentTemplateVersion

    def _base_query(self) -> Select[tuple[DocumentTemplateVersion]]:
        stmt = select(self.model).where(self.model.deleted_at.is_(None))
        if self.clinic_id is None:
            return stmt.where(false())
        return stmt.where(
            or_(
                self.model.clinic_id == self.clinic_id,
                self.model.clinic_id.is_(None),
            )
        )

    async def latest(
        self,
        *,
        template_id: int,
        locale: str,
    ) -> DocumentTemplateVersion | None:
        result = await self.session.execute(
            self._base_query()
            .where(
                self.model.document_template_id == template_id,
                self.model.locale == locale,
                self.model.published_at.is_not(None),
            )
            .order_by(desc(self.model.version))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def next_version(self, *, template_id: int, locale: str) -> int:
        result = await self.session.execute(
            select(func.max(self.model.version)).where(
                self.model.document_template_id == template_id,
                self.model.locale == locale,
                self.model.deleted_at.is_(None),
            )
        )
        current = result.scalar_one()
        return int(current or 0) + 1

    async def get_for_template(
        self,
        *,
        template_id: int,
        version_id: int,
    ) -> DocumentTemplateVersion | None:
        result = await self.session.execute(
            self._base_query().where(
                self.model.id == version_id,
                self.model.document_template_id == template_id,
            )
        )
        return result.scalar_one_or_none()


class DocumentRepository(BaseRepository[Document]):
    model = Document

    async def list_for_patient(
        self,
        *,
        patient_id: int,
        page: PaginationParams | None,
    ) -> Page[Document]:
        resolved = normalize_pagination(page)
        stmt = self._base_query().where(self.model.patient_id == patient_id)
        total = (
            await self.session.execute(
                select(func.count()).select_from(stmt.subquery())
            )
        ).scalar_one()
        stmt = stmt.order_by(desc(self.model.created_at), desc(self.model.id))
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


class DocumentRecipientRepository(BaseRepository[DocumentRecipient]):
    model = DocumentRecipient

    async def list_for_document(self, document_id: int) -> list[DocumentRecipient]:
        result = await self.session.scalars(
            self._base_query().where(self.model.document_id == document_id)
        )
        return list(result.all())
