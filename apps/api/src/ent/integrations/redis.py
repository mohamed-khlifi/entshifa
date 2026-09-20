"""Redis connectivity helpers."""

from __future__ import annotations

from redis.asyncio import Redis

from ent.settings import Settings


async def ping_redis(settings: Settings) -> None:
    client: Redis = Redis.from_url(settings.redis_url, socket_connect_timeout=5)
    try:
        await client.ping()
    finally:
        await client.aclose()
