import httpx
from gotenberg_api import GotenbergServerError, ScreenshotHTMLRequest

from env_settings import settings
from logging_config import get_logger

logger = get_logger(__name__)


async def render_screenshot(client: httpx.AsyncClient, html_code: str) -> bytes:
    gotenberg = settings.gotenberg
    try:
        request = ScreenshotHTMLRequest(
            index_html=html_code,
            width=gotenberg.width,
            format=gotenberg.default_screenshot_format,
            wait_delay=gotenberg.wait_delay,
        )
        return await request.asend(client)
    except GotenbergServerError as exc:
        logger.error("ОШИБКА СКРИНШОТА: %s", exc)
        raise
