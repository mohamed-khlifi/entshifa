"""Encounter template service: 3-tier resolution, complaint routing, and overrides."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.audit.recorder import AuditRecorder
from ent.core.context import set_clinic_id, set_user_id
from ent.core.errors.exceptions import PermissionDeniedError, ValidationError
from ent.core.schemas.common import CodeableConcept
from ent.core.security.permissions import Permission
from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.encounters.exceptions import EncounterTemplateNotFoundError
from ent.features.encounters.mapping import template_to_read
from ent.features.encounters.models import EncounterTemplate
from ent.features.encounters.references import EncounterReferences
from ent.features.encounters.repository import EncounterTemplateRepository
from ent.features.encounters.schemas.requests import (
    EncounterTemplateOverrideWrite,
    EncounterTemplateRouteRequest,
)
from ent.features.encounters.schemas.responses import EncounterTemplateRead
from ent.features.terminology.models import Concept


class EncounterTemplateService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit = AuditRecorder(session)
        self._refs = EncounterReferences(session)

    def _bind(self, user: CurrentUser) -> None:
        set_clinic_id(user.clinic_id)
        set_user_id(user.user_id)

    def _repo(self, clinic_id: int | None) -> EncounterTemplateRepository:
        return EncounterTemplateRepository(self._session, clinic_id=clinic_id)

    async def _resolve_concepts(
        self,
        user: CurrentUser,
        concept_ids: list[int | str],
        content_locale: str,
    ) -> list[CodeableConcept]:
        int_ids = {int(cid) for cid in concept_ids if str(cid).isdigit()}
        if not int_ids:
            return []
        labels = await self._refs.labels(user, int_ids, content_locale)
        results: list[CodeableConcept] = []
        for cid in int_ids:
            item = labels.get(cid)
            if item:
                pub_id, code, display = item
                results.append(
                    CodeableConcept(concept_id=pub_id, code=code, display=display)
                )
        return results

    async def _to_read(
        self,
        user: CurrentUser,
        template: EncounterTemplate,
        content_locale: str,
    ) -> EncounterTemplateRead:
        trigger_concepts = await self._resolve_concepts(
            user, template.trigger_concept_ids or [], content_locale
        )
        return template_to_read(template, trigger_concepts)

    async def list_templates(
        self,
        *,
        user: CurrentUser,
        content_locale: str,
    ) -> list[EncounterTemplateRead]:
        """List active templates visible to this doctor/clinic with overrides taking precedence."""
        self._bind(user)
        repo = self._repo(user.clinic_id)
        rows = await repo.list_effective_for_user(user_id=user.user_id)
        return [await self._to_read(user, row, content_locale) for row in rows]

    async def get_by_public_id(
        self,
        *,
        user: CurrentUser,
        public_id: str,
        content_locale: str,
    ) -> EncounterTemplateRead:
        self._bind(user)
        repo = self._repo(user.clinic_id)
        row = await repo.get_active_for_user(public_id, user_id=user.user_id)
        if row is None:
            raise EncounterTemplateNotFoundError(publicId=public_id)
        return await self._to_read(user, row, content_locale)

    async def get_effective_by_code(
        self,
        *,
        user: CurrentUser,
        code: str,
        content_locale: str,
    ) -> EncounterTemplateRead:
        self._bind(user)
        repo = self._repo(user.clinic_id)
        row = await repo.get_effective_by_code(code, user_id=user.user_id)
        if row is None:
            raise EncounterTemplateNotFoundError(code=code)
        return await self._to_read(user, row, content_locale)

    async def route_by_complaint(
        self,
        *,
        user: CurrentUser,
        body: EncounterTemplateRouteRequest,
        content_locale: str,
    ) -> EncounterTemplateRead:
        """Route chief complaints to the most relevant encounter template.

        Doctor override > clinic override > system template.
        If no primary complaint matches, returns the first matching template or general template.
        """
        self._bind(user)
        repo = self._repo(user.clinic_id)
        target_codes = body.complaint_codes
        if body.primary_complaint_code:
            target_codes = [body.primary_complaint_code] + [
                c for c in target_codes if c != body.primary_complaint_code
            ]

        # Resolve concept IDs for target complaint codes
        if target_codes:
            concepts = (
                (
                    await self._session.execute(
                        select(Concept).where(
                            Concept.code.in_(target_codes),
                            Concept.deleted_at.is_(None),
                        )
                    )
                )
                .scalars()
                .all()
            )
            concept_by_code = {c.code: c for c in concepts}

            for code in target_codes:
                concept = concept_by_code.get(code)
                if concept is not None:
                    matched = await repo.get_effective_for_concept(
                        int(concept.id), user_id=user.user_id
                    )
                    if matched is not None:
                        return await self._to_read(user, matched, content_locale)

        # Fallback 1: general consultation template if exists
        general = await repo.get_effective_by_code(
            "TPL.GENERAL_CONSULTATION", user_id=user.user_id
        )
        if general is not None:
            return await self._to_read(user, general, content_locale)

        # Fallback 2: first available active template
        all_templates = await repo.list_effective_for_user(user_id=user.user_id)
        if all_templates:
            return await self._to_read(user, all_templates[0], content_locale)

        raise EncounterTemplateNotFoundError(reason="no_templates_available")

    async def override_template(
        self,
        *,
        user: CurrentUser,
        base_code: str,
        body: EncounterTemplateOverrideWrite,
        content_locale: str,
        scope: str = "doctor",
    ) -> EncounterTemplateRead:
        """Create or update a doctor-specific or clinic-wide template override."""
        self._bind(user)
        repo = self._repo(user.clinic_id)
        base_template = await repo.get_effective_by_code(
            base_code, user_id=user.user_id
        )
        if base_template is None:
            raise EncounterTemplateNotFoundError(code=base_code)

        if scope == "clinic":
            if Permission.ADMIN_TEMPLATES not in user.permissions:
                raise PermissionDeniedError(permission=Permission.ADMIN_TEMPLATES)
            target_user_id: int | None = None
        elif scope == "doctor":
            target_user_id = user.user_id
        else:
            raise ValidationError(reason="invalid_scope")

        # Resolve trigger concepts if provided
        trigger_ids: list[int] = []
        if body.trigger_concept_codes is not None:
            concepts = (
                (
                    await self._session.execute(
                        select(Concept).where(
                            Concept.code.in_(body.trigger_concept_codes),
                            Concept.deleted_at.is_(None),
                        )
                    )
                )
                .scalars()
                .all()
            )
            trigger_ids = [int(c.id) for c in concepts]
        else:
            trigger_ids = [
                int(cid) for cid in (base_template.trigger_concept_ids or [])
            ]

        name_key = body.name_key or base_template.name_key
        config_dict = body.config.model_dump(by_alias=True)

        existing = await repo.get_exact_override(
            base_code,
            clinic_id=user.clinic_id,
            user_id=target_user_id,
        )

        if existing is not None:
            existing.name_key = name_key
            existing.trigger_concept_ids = trigger_ids
            existing.config = config_dict
            existing.is_active = True
            existing.updated_by_id = user.user_id
            target_row = existing
        else:
            target_row = EncounterTemplate(
                public_id=new_ulid(),
                clinic_id=user.clinic_id,
                user_id=target_user_id,
                code=base_code,
                name_key=name_key,
                trigger_concept_ids=trigger_ids,
                config=config_dict,
                is_active=True,
                created_by_id=user.user_id,
                updated_by_id=user.user_id,
            )
            self._session.add(target_row)

        await self._session.flush()
        self._audit.record_access(
            action="override",
            entity_type="encounter_template",
            clinic_id=user.clinic_id,
            entity_id=int(target_row.id),
            entity_public_id=target_row.public_id,
        )
        await self._session.commit()
        # Reload cleanly in async context to populate server defaults and computed columns
        reloaded = await repo.get_active_for_user(
            target_row.public_id, user_id=user.user_id
        )
        if reloaded is None:
            raise EncounterTemplateNotFoundError(publicId=target_row.public_id)
        return await self._to_read(user, reloaded, content_locale)

    async def reset_override(
        self,
        *,
        user: CurrentUser,
        base_code: str,
        scope: str = "doctor",
    ) -> None:
        """Reset (soft delete) a doctor or clinic override, restoring lower precedence template."""
        self._bind(user)
        repo = self._repo(user.clinic_id)
        if scope == "clinic":
            if Permission.ADMIN_TEMPLATES not in user.permissions:
                raise PermissionDeniedError(permission=Permission.ADMIN_TEMPLATES)
            target_user_id: int | None = None
        elif scope == "doctor":
            target_user_id = user.user_id
        else:
            raise ValidationError(reason="invalid_scope")

        existing = await repo.get_exact_override(
            base_code,
            clinic_id=user.clinic_id,
            user_id=target_user_id,
        )
        if existing is None:
            raise EncounterTemplateNotFoundError(code=base_code)

        await repo.soft_delete(int(existing.id), by_user_id=user.user_id)
        self._audit.record_access(
            action="reset_override",
            entity_type="encounter_template",
            clinic_id=user.clinic_id,
            entity_id=int(existing.id),
            entity_public_id=existing.public_id,
        )
        await self._session.commit()
