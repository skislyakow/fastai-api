import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import AnyHttpUrl

from env_settings import settings
from gotenberg_client import GotenbergServerError, render_screenshot
from page_generator import SITE_HTML_PATH, stream_site_html
from s3_client import SCREENSHOT_KEY, build_object_url, build_site_html_key, upload_html, upload_screenshot
from schemas import SiteResponse

SITES: dict[int, SiteResponse] = {}
BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


def s3_urls(site_id: int) -> tuple[AnyHttpUrl, AnyHttpUrl, AnyHttpUrl]:
    s3 = settings.s3
    endpoint_url = str(s3.endpoint_url)
    html_key = build_site_html_key(site_id)
    html_url = build_object_url(endpoint_url, s3.bucket_name, html_key)
    download_url = build_object_url(
        endpoint_url,
        s3.bucket_name,
        html_key,
        attachment_filename="index.html",
    )
    screenshot_url = build_object_url(endpoint_url, s3.bucket_name, SCREENSHOT_KEY)
    return AnyHttpUrl(html_url), AnyHttpUrl(download_url), AnyHttpUrl(screenshot_url)


def get_next_id() -> int:
    return max(SITES, default=0) + 1


def run_in_background(coro: Any) -> None:
    task = asyncio.create_task(coro)
    BACKGROUND_TASKS.add(task)
    task.add_done_callback(BACKGROUND_TASKS.discard)


async def cancel_background_tasks() -> None:
    tasks = list(BACKGROUND_TASKS)
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


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
            try:
                screenshot_bytes = await render_screenshot(gotenberg, html_code)
                await upload_screenshot(
                    s3,
                    bucket,
                    SCREENSHOT_KEY,
                    screenshot_bytes,
                )
            except GotenbergServerError:
                pass
        if site_id in SITES:
            SITES[site_id] = SITES[site_id].model_copy(
                update={"updated_at": datetime.now(UTC)},
            )
    finally:
        await queue.put(None)


async def stream_queue(queue: asyncio.Queue[str | None]) -> AsyncGenerator[str]:
    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        yield chunk


def build_site(
    site_id: int,
    *,
    title: str,
    prompt: str,
) -> SiteResponse:
    html_url, download_url, screenshot_url = s3_urls(site_id)
    now = datetime.now(UTC)
    return SiteResponse(
        id=site_id,
        title=title,
        html_code_url=html_url,
        html_code_download_url=download_url,
        screenshot_url=screenshot_url,
        prompt=prompt,
        created_at=now,
        updated_at=now,
    )


def mock_site(site_id: int = 1) -> SiteResponse:
    html_url, download_url, screenshot_url = s3_urls(site_id)
    return SiteResponse(
        id=site_id,
        title="Стегозавры",
        html_code_url=html_url,
        html_code_download_url=download_url,
        screenshot_url=screenshot_url,
        prompt="Сделай сайт про Стегозавров",
        created_at=datetime(2025, 6, 15, 18, 29, 56, tzinfo=UTC),
        updated_at=datetime(2025, 6, 15, 18, 29, 56, tzinfo=UTC),
    )
