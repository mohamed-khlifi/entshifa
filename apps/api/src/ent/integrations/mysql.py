"""MySQL connectivity helpers (readiness checks until P0-03 session layer)."""

from __future__ import annotations

import aiomysql

from ent.settings import Settings


async def ping_mysql(settings: Settings) -> None:
    conn = await aiomysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        db=settings.mysql_database,
        connect_timeout=5,
    )
    try:
        await conn.ping(reconnect=False)
    finally:
        conn.close()
