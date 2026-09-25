import json
from typing import Any
from urllib.parse import quote, urlencode

from botocore.exceptions import ClientError

SCREENSHOT_KEY = "screenshot.jpg"


def site_html_key(site_id: int) -> str:
    return f"sites/{site_id}/index.html"


def public_policy(bucket: str) -> str:
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


async def upload_html(s3: Any, bucket: str, key: str, html_code: str) -> None:
    await s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=html_code.encode("utf-8"),
        ContentType="text/html",
        ContentDisposition="inline",
    )
