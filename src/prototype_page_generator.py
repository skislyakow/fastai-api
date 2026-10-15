import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx
from html_page_generator import AsyncDeepseekClient, AsyncUnsplashClient

from env_settings import settings
from logging_config import get_logger, setup_logging
from page_generator import (
    DEFAULT_PROMPT,
    StreamPageGenerator,
    build_deepseek_client_kwargs,
    build_unsplash_client_kwargs,
)

logger = get_logger(__name__)

MAX_ATTEMPTS = 3
TMP_DIR = Path(__file__).resolve().parent.parent / "tmp"


def sanitize_filename(title: str) -> str:
    forbidden = '<>:"/\\|?*'
    cleaned = "".join(char if char not in forbidden else " " for char in title)
    cleaned = " ".join(cleaned.split()).strip()
    return cleaned or "site"


async def generate_page(prompt: str) -> None:
    async with (
        AsyncUnsplashClient.setup(
            settings.unsplash.api_key.get_secret_value(),
            timeout=settings.unsplash.timeout,
            **build_unsplash_client_kwargs(),
        ),
        AsyncDeepseekClient.setup(
            settings.deepseek.api_key.get_secret_value(),
            timeout=settings.deepseek.timeout,
            **build_deepseek_client_kwargs(),
        ),
    ):
        generator = StreamPageGenerator(debug_mode=settings.debug)
        async for chunk in generator(prompt):
            logger.debug("%s", chunk)

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TMP_DIR / f"{sanitize_filename(generator.html_page.title)}.html"
    output_path.write_text(generator.html_page.html_code, encoding="utf-8")
    logger.info("Файл сохранён: %s", output_path)


def main() -> None:
    setup_logging(debug=settings.debug)
    parser = argparse.ArgumentParser(description="Сгенерировать HTML-страницу по промпту")
    parser.add_argument("prompt", nargs="?", default=DEFAULT_PROMPT)
    args = parser.parse_args()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            asyncio.run(generate_page(args.prompt))
            return
        except (json.decoder.JSONDecodeError, httpx.HTTPError) as exc:
            logger.warning("Попытка %s/%s: %s", attempt, MAX_ATTEMPTS, exc)

    logger.error("Генерация не удалась после нескольких попыток.")
    sys.exit(1)


if __name__ == "__main__":
    main()
