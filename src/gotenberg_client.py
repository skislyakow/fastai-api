import sys

import httpx
from gotenberg_api import GotenbergServerError, ScreenshotHTMLRequest

from env_settings import settings


async def render_screenshot(html_code: str) -> bytes | None:
    gotenberg = settings.gotenberg
    timeout = gotenberg.timeout
    try:
        async with httpx.AsyncClient(
            base_url=gotenberg.endpoint_url,
            timeout=timeout,
            limits=httpx.Limits(max_connections=gotenberg.max_connections),
        ) as client:
            request = ScreenshotHTMLRequest(
                index_html=html_code,
                width=gotenberg.width,
                format=gotenberg.default_screenshot_format,
                wait_delay=gotenberg.wait_delay,
            )
            return await request.asend(client)
    except GotenbergServerError as exc:
        print(f"[ОШИБКА СКРИНШОТА] {exc}", file=sys.stderr)
        return None
