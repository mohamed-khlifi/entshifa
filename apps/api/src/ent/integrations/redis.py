"""Redis client factory."""

from __future__ import annotations

from redis.asyncio import Redis

from ent.settings import Settings, get_settings

_client: Redis | None = None


async def get_redis(settings: Settings | None = None) -> Redis:
    global _client
    if _client is None:
        resolved = settings or get_settings()
        _client = Redis.from_url(resolved.redis_url, decode_responses=True)
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
    _client = None


async def ping_redis(settings: Settings) -> None:
    client = Redis.from_url(settings.redis_url, socket_connect_timeout=5)
    try:
        await client.ping()
    finally:
        await client.aclose()
