import httpx
from gotenberg_api import GotenbergServerError, ScreenshotHTMLRequest

from config.env_settings import GotenbergSettings
from config.logging_config import get_logger

logger = get_logger(__name__)


async def render_screenshot(
    client: httpx.AsyncClient,
    html_code: str,
    gotenberg_settings: GotenbergSettings,
) -> bytes:
    try:
        request = ScreenshotHTMLRequest(
            index_html=html_code,
            width=gotenberg_settings.width,
            format=gotenberg_settings.default_screenshot_format,
            wait_delay=gotenberg_settings.wait_delay,
        )
        return await request.asend(client)
    except GotenbergServerError as exc:
        logger.error("ОШИБКА СКРИНШОТА: %s", exc)
        raise
