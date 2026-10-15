import json
from typing import Any
from urllib.parse import quote, urlencode

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from env_settings import settings


def build_site_html_key(site_id: int) -> str:
    return f"sites/{site_id}/index.html"


def build_public_policy(bucket: str) -> str:
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                "Resource": [f"arn:aws:s3:::{bucket}"],
            },
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket}/*"],
            },
        ],
    }
    return json.dumps(policy)


def build_object_url(
    endpoint_url: str,
    bucket: str,
    key: str,
    *,
    attachment_filename: str | None = None,
) -> str:
    base_url = f"{endpoint_url.rstrip('/')}/{quote(bucket)}/{quote(key)}"
    if attachment_filename is None:
        return base_url
    query = urlencode(
        {
            "response-content-disposition": f'attachment; filename="{attachment_filename}"',
        },
    )
    return f"{base_url}?{query}"


def create_s3_client() -> Any:
    config_kwargs: dict[str, Any] = {"signature_version": "s3v4"}
    for src, dst in (
        (settings.s3.connect_timeout, "connect_timeout"),
        (settings.s3.read_timeout, "read_timeout"),
        (settings.s3.max_pool_connections, "max_pool_connections"),
    ):
        if src is not None:
            config_kwargs[dst] = src

    return aioboto3.Session().client(
        "s3",
        endpoint_url=str(settings.s3.endpoint_url),
        aws_access_key_id=settings.s3.access_key_id.get_secret_value(),
        aws_secret_access_key=settings.s3.secret_access_key.get_secret_value(),
        region_name=settings.s3.region_name,
        config=Config(**config_kwargs),
    )


async def ensure_bucket(s3: Any, bucket: str) -> None:
    try:
        await s3.head_bucket(Bucket=bucket)
    except ClientError:
        await s3.create_bucket(Bucket=bucket)
    await s3.put_bucket_policy(Bucket=bucket, Policy=build_public_policy(bucket))


async def upload_html(s3: Any, bucket: str, key: str, html_code: str) -> None:
    await s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=html_code.encode("utf-8"),
        ContentType="text/html",
        ContentDisposition="inline",
    )


async def upload_screenshot(
    s3: Any,
    bucket: str,
    key: str,
    content_bytes: bytes,
    content_type: str,
) -> None:
    await s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=content_bytes,
        ContentType=content_type,
        ContentDisposition="inline",
    )
