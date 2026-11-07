"""Rate limiting for public questionnaire token endpoints (architecture §36)."""

from __future__ import annotations

from redis.asyncio import Redis

from ent.features.questionnaires.exceptions import QuestionnaireRateLimitedError
from ent.integrations.redis import get_redis

_IP_WINDOW_SECONDS = 900
_IP_MAX_REQUESTS = 60
_TOKEN_WINDOW_SECONDS = 900
_TOKEN_MAX_REQUESTS = 20


async def assert_public_questionnaire_allowed(
    *,
    ip_address: str | None,
    token_hash: str,
) -> None:
    client = await get_redis()
    if ip_address:
        ip_key = f"questionnaire:public:ip:{ip_address}"
        if await _is_over_limit(client, ip_key, _IP_MAX_REQUESTS):
            raise QuestionnaireRateLimitedError(scope="ip")
        await _increment(client, ip_key, _IP_WINDOW_SECONDS)

    token_key = f"questionnaire:public:token:{token_hash}"
    if await _is_over_limit(client, token_key, _TOKEN_MAX_REQUESTS):
        raise QuestionnaireRateLimitedError(scope="token")
    await _increment(client, token_key, _TOKEN_WINDOW_SECONDS)


async def _is_over_limit(client: Redis, key: str, maximum: int) -> bool:
    raw = await client.get(key)
    if raw is None:
        return False
    return int(raw) >= maximum


async def _increment(client: Redis, key: str, window_seconds: int) -> None:
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, window_seconds)
