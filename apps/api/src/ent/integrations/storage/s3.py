"""S3-compatible object storage connectivity (expanded in P0-13)."""

from __future__ import annotations

from aiobotocore.session import get_session
from botocore.config import Config

from ent.settings import Settings


async def ping_storage(settings: Settings) -> None:
    session = get_session()
    config = Config(
        s3={"addressing_style": "path"},
        connect_timeout=5,
        read_timeout=5,
    )
    async with session.create_client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        config=config,
    ) as client:
        await client.head_bucket(Bucket=settings.s3_bucket)
