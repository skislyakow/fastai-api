import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from clients.gotenberg import render_screenshot
from clients.s3 import (
    build_screenshot_key,
    build_site_html_key,
    get_screenshot_content_type,
    upload_html,
    upload_screenshot,
)
from config.env_settings import Settings
from services.page_generator import SITE_HTML_PATH, stream_site_html
from services.sites import update_site_timestamp


async def relay_html(
    queue: asyncio.Queue[str | None],
    *,
    prompt: str,
    s3: Any,
    gotenberg: httpx.AsyncClient,
    app_settings: Settings,
    site_id: int,
) -> None:
    bucket = app_settings.s3.bucket_name
    screenshot_format = app_settings.gotenberg.default_screenshot_format
    try:
        async for chunk in stream_site_html(prompt, debug=app_settings.debug):
            await queue.put(chunk)
        if SITE_HTML_PATH.exists():
            html_code = SITE_HTML_PATH.read_text(encoding="utf-8")
            await upload_html(s3, bucket, build_site_html_key(site_id), html_code)
            screenshot_bytes = await render_screenshot(
                gotenberg,
                html_code,
                app_settings.gotenberg,
            )
            await upload_screenshot(
                s3,
                bucket,
                build_screenshot_key(screenshot_format),
                screenshot_bytes,
                get_screenshot_content_type(screenshot_format),
            )
        update_site_timestamp(site_id)
    finally:
        await queue.put(None)


async def stream_queue(queue: asyncio.Queue[str | None]) -> AsyncGenerator[str]:
    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        yield chunk
