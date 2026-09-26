"""S3-compatible object storage (MinIO locally, S3 in staging/prod)."""

from __future__ import annotations

from typing import Any

from aiobotocore.session import get_session
from botocore.config import Config
from botocore.exceptions import ClientError

from ent.integrations.storage.port import PresignedUrl
from ent.settings import Settings


def _client_kwargs(settings: Settings) -> dict[str, Any]:
    return {
        "endpoint_url": settings.s3_endpoint,
        "region_name": settings.s3_region,
        "aws_access_key_id": settings.s3_access_key_id,
        "aws_secret_access_key": settings.s3_secret_access_key,
        "config": Config(
            s3={"addressing_style": "path"},
            signature_version="s3v4",
            connect_timeout=10,
            read_timeout=60,
        ),
    }


class S3ObjectStorage:
    """Pre-signed upload/download against an S3-compatible bucket."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._bucket = settings.s3_bucket

    async def ping(self) -> None:
        session = get_session()
        async with session.create_client("s3", **_client_kwargs(self._settings)) as client:
            await client.head_bucket(Bucket=self._bucket)

    async def create_presigned_upload(
        self,
        *,
        key: str,
        content_type: str,
        expires_in_seconds: int,
    ) -> PresignedUrl:
        session = get_session()
        async with session.create_client("s3", **_client_kwargs(self._settings)) as client:
            url = await client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": self._bucket,
                    "Key": key,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in_seconds,
                HttpMethod="PUT",
            )
        return PresignedUrl(
            url=url,
            method="PUT",
            expires_in_seconds=expires_in_seconds,
            headers={"Content-Type": content_type},
        )

    async def create_presigned_download(
        self,
        *,
        key: str,
        expires_in_seconds: int,
        filename: str | None = None,
    ) -> PresignedUrl:
        params: dict[str, Any] = {"Bucket": self._bucket, "Key": key}
        if filename:
            params["ResponseContentDisposition"] = f'inline; filename="{filename}"'
        session = get_session()
        async with session.create_client("s3", **_client_kwargs(self._settings)) as client:
            url = await client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expires_in_seconds,
                HttpMethod="GET",
            )
        return PresignedUrl(
            url=url,
            method="GET",
            expires_in_seconds=expires_in_seconds,
            headers={},
        )

    async def object_exists(self, *, key: str) -> bool:
        session = get_session()
        async with session.create_client("s3", **_client_kwargs(self._settings)) as client:
            try:
                await client.head_object(Bucket=self._bucket, Key=key)
            except ClientError as exc:
                code = str(exc.response.get("Error", {}).get("Code", ""))
                if code in {"404", "NoSuchKey", "NotFound"}:
                    return False
                raise
            return True

    async def get_object_bytes(self, *, key: str) -> bytes:
        session = get_session()
        async with session.create_client("s3", **_client_kwargs(self._settings)) as client:
            response = await client.get_object(Bucket=self._bucket, Key=key)
            body = response["Body"]
            payload = await body.read()
            return bytes(payload)

    async def put_object_bytes(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str,
    ) -> None:
        session = get_session()
        async with session.create_client("s3", **_client_kwargs(self._settings)) as client:
            await client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )

    async def delete_object(self, *, key: str) -> None:
        session = get_session()
        async with session.create_client("s3", **_client_kwargs(self._settings)) as client:
            await client.delete_object(Bucket=self._bucket, Key=key)


async def ping_storage(settings: Settings) -> None:
    """Health-check helper used by /health/ready."""

    await S3ObjectStorage(settings).ping()
