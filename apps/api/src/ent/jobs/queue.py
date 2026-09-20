"""Redis-backed job queue (uses existing redis client; no Celery/ARQ dependency)."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, cast

from ent.integrations.redis import get_redis

logger = logging.getLogger(__name__)

QUEUE_KEY = "ent:jobs:queue"
DELAYED_KEY = "ent:jobs:delayed"
EFFECT_KEY_PREFIX = "ent:jobs:effect:"


async def enqueue_job(
    *,
    job_name: str,
    idempotency_key: str,
    payload: dict[str, Any] | None = None,
    delay_seconds: float = 0,
) -> None:
    """Push a job message onto the Redis queue (or delayed set)."""

    message = json.dumps(
        {
            "job_name": job_name,
            "idempotency_key": idempotency_key,
            "payload": payload or {},
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    client = await get_redis()
    if delay_seconds > 0:
        score = time.time() + delay_seconds
        await client.zadd(DELAYED_KEY, {message: score})
        return
    await client.lpush(QUEUE_KEY, message)  # type: ignore[misc]


async def promote_delayed_jobs() -> int:
    """Move due delayed messages onto the ready queue. Returns count moved."""

    client = await get_redis()
    now = time.time()
    due = cast(list[str], await client.zrangebyscore(DELAYED_KEY, min="-inf", max=now))
    if not due:
        return 0
    moved = 0
    for message in due:
        removed = int(cast(int, await client.zrem(DELAYED_KEY, message)))
        if removed:
            await client.lpush(QUEUE_KEY, message)  # type: ignore[misc]
            moved += 1
    return moved


async def dequeue_job(*, timeout_seconds: int = 1) -> dict[str, Any] | None:
    """Blocking pop from the ready queue. Returns None on timeout."""

    await promote_delayed_jobs()
    client = await get_redis()
    item = cast(
        tuple[str, str] | None,
        await client.brpop([QUEUE_KEY], timeout=timeout_seconds),  # type: ignore[misc]
    )
    if item is None:
        return None
    _key, raw = item
    data = json.loads(raw)
    if not isinstance(data, dict):
        logger.warning("Ignoring non-object job payload: %s", raw)
        return None
    return data


async def record_side_effect(idempotency_key: str) -> int:
    """Increment a Redis counter used by tests to prove the job body ran once."""

    client = await get_redis()
    return int(cast(int, await client.incr(f"{EFFECT_KEY_PREFIX}{idempotency_key}")))


async def get_side_effect_count(idempotency_key: str) -> int:
    client = await get_redis()
    value = cast(str | None, await client.get(f"{EFFECT_KEY_PREFIX}{idempotency_key}"))
    return int(value) if value is not None else 0
