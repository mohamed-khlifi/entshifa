"""Login throttling using Redis (per account and per IP)."""

from __future__ import annotations

from redis.asyncio import Redis

from ent.core.errors.exceptions import AuthRateLimitedError
from ent.integrations.redis import get_redis

_ACCOUNT_WINDOW_SECONDS = 900
_ACCOUNT_MAX_ATTEMPTS = 10
_IP_WINDOW_SECONDS = 900
_IP_MAX_ATTEMPTS = 30


async def assert_login_allowed(*, email: str, ip_address: str | None) -> None:
    client = await get_redis()
    account_key = f"auth:login:account:{email.lower()}"
    if await _is_over_limit(client, account_key, _ACCOUNT_MAX_ATTEMPTS):
        raise AuthRateLimitedError(scope="account")

    if ip_address:
        ip_key = f"auth:login:ip:{ip_address}"
        if await _is_over_limit(client, ip_key, _IP_MAX_ATTEMPTS):
            raise AuthRateLimitedError(scope="ip")


async def record_failed_login(*, email: str, ip_address: str | None) -> None:
    client = await get_redis()
    await _increment(
        client, f"auth:login:account:{email.lower()}", _ACCOUNT_WINDOW_SECONDS
    )
    if ip_address:
        await _increment(client, f"auth:login:ip:{ip_address}", _IP_WINDOW_SECONDS)


async def clear_login_attempts(*, email: str, ip_address: str | None) -> None:
    client = await get_redis()
    await client.delete(f"auth:login:account:{email.lower()}")
    if ip_address:
        await client.delete(f"auth:login:ip:{ip_address}")


async def _is_over_limit(client: Redis, key: str, maximum: int) -> bool:
    raw = await client.get(key)
    if raw is None:
        return False
    return int(raw) >= maximum


async def _increment(client: Redis, key: str, window_seconds: int) -> None:
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, window_seconds)
