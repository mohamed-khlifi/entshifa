"""Shared idempotency helpers for audiology POST creates."""

from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.security.principal import CurrentUser
from ent.core.utils.ids import new_ulid
from ent.features.audiology.exceptions import AudiogramIdempotencyMismatchError
from ent.features.audiology.models import AudiologyRequestIdempotency
from ent.features.audiology.repository import AudiologyIdempotencyRepository


def hash_body(body: BaseModel) -> str:
    raw = json.dumps(
        body.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def replay_idempotent(
    session: AsyncSession,
    user: CurrentUser,
    *,
    key: str | None,
    body: BaseModel,
    resource_type: str,
) -> str | None:
    if not key:
        return None
    existing = await AudiologyIdempotencyRepository(
        session, clinic_id=user.clinic_id
    ).get_by_key(key)
    if existing is None:
        return None
    if (
        existing.request_hash != hash_body(body)
        or existing.resource_type != resource_type
    ):
        raise AudiogramIdempotencyMismatchError()
    return existing.resource_public_id


async def store_idempotent(
    session: AsyncSession,
    user: CurrentUser,
    *,
    key: str | None,
    body: BaseModel,
    resource_type: str,
    resource_public_id: str,
) -> None:
    if not key:
        return
    await AudiologyIdempotencyRepository(session, clinic_id=user.clinic_id).add(
        AudiologyRequestIdempotency(
            public_id=new_ulid(),
            clinic_id=user.clinic_id,
            idempotency_key=key,
            request_hash=hash_body(body),
            resource_type=resource_type,
            resource_public_id=resource_public_id,
        )
    )
