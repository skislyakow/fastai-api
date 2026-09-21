import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError

from env_settings import settings

STUB_DIR = Path(__file__).resolve().parent.parent / "stub"
UPLOADS = [
    ("index.html", "hello.html", "text/html", "inline"),
    ("screenshot.jpg", "screenshot.jpg", "image/jpeg", "inline"),
]


def public_policy(bucket: str) -> str:
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket}/*"],
            },
        ],
    }
    return json.dumps(policy)


def object_url(
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


async def ensure_bucket(s3: Any, bucket: str) -> None:
    try:
        await s3.head_bucket(Bucket=bucket)
    except ClientError:
        await s3.create_bucket(Bucket=bucket)
    await s3.put_bucket_policy(Bucket=bucket, Policy=public_policy(bucket))
    print(f"[bucket] {bucket} - публичная политика применена")


async def upload(
    s3: Any,
    bucket: str,
    source: Path,
    key: str,
    content_type: str,
    content_disposition: str,
) -> None:
    body = source.read_bytes()
    await s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType=content_type,
        ContentDisposition=content_disposition,
    )
    print(
        f"[upload] {source.name} -> {key} ({content_type}, {content_disposition}, {len(body)} B)",
    )


async def print_head(s3: Any, bucket: str, key: str) -> None:
    info = await s3.head_object(Bucket=bucket, Key=key)
    disposition = info.get("ContentDisposition") or "-"
    print(
        f"[head] {key}: ContentType={info['ContentType']}, "
        f"ContentDisposition={disposition}, ContentLength={info['ContentLength']}",
    )


async def main() -> None:
    s3_settings = settings.s3
    if s3_settings is None:
        print("S3__* не заданы в .env - заполните из example.env", file=sys.stderr)
        sys.exit(1)

    access_key_id = s3_settings.access_key_id
    secret_access_key = s3_settings.secret_access_key
    if access_key_id is None or secret_access_key is None:
        print("S3__ACCESS_KEY_ID и S3__SECRET_ACCESS_KEY обязательны", file=sys.stderr)
        sys.exit(1)

    bucket = s3_settings.bucket_name
    endpoint_url = s3_settings.endpoint_url

    s3_cm: Any = aioboto3.Session().client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id.get_secret_value(),
        aws_secret_access_key=secret_access_key.get_secret_value(),
        region_name=s3_settings.region_name,
        config=Config(signature_version="s3v4"),
    )
    async with s3_cm as s3:
        await ensure_bucket(s3, bucket)

        for source_name, key, content_type, content_disposition in UPLOADS:
            await upload(
                s3,
                bucket,
                source=STUB_DIR / source_name,
                key=key,
                content_type=content_type,
                content_disposition=content_disposition,
            )

        await print_head(s3, bucket, "hello.html")

        print(f"\n[url] {object_url(endpoint_url, bucket, 'hello.html')}")
        print(
            "[url] " + object_url(endpoint_url, bucket, "hello.html", attachment_filename="hello.html"),
        )
        print(f"[url] {object_url(endpoint_url, bucket, 'screenshot.jpg')}")


def main_entry() -> None:
    parser = argparse.ArgumentParser(
        description="S3-прототип: ensure_bucket, upload, head, URL (MinIO)",
    )
    parser.parse_args()
    asyncio.run(main())


if __name__ == "__main__":
    main_entry()
