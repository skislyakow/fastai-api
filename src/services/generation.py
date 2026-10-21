import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from clients.gotenberg import render_screenshot
from clients.s3 import SCREENSHOT_KEY, SCREENSHOT_MIME, build_site_html_key, upload_html, upload_screenshot
from services.page_generator import SITE_HTML_PATH, stream_site_html
from services.sites import update_site_timestamp


async def relay_html(
    queue: asyncio.Queue[str | None],
    *,
    prompt: str,
    s3: Any,
    gotenberg: httpx.AsyncClient,
    bucket: str,
    site_id: int,
) -> None:
    try:
        async for chunk in stream_site_html(prompt):
            await queue.put(chunk)
        if SITE_HTML_PATH.exists():
            html_code = SITE_HTML_PATH.read_text(encoding="utf-8")
            await upload_html(s3, bucket, build_site_html_key(site_id), html_code)
            screenshot_bytes = await render_screenshot(gotenberg, html_code)
            await upload_screenshot(
                s3,
                bucket,
                SCREENSHOT_KEY,
                screenshot_bytes,
                SCREENSHOT_MIME,
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
