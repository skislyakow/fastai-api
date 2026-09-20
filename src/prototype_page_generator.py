import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx
from html_page_generator import AsyncDeepseekClient, AsyncUnsplashClient

from env_settings import settings
from page_generator import (
    DEFAULT_PROMPT,
    StreamPageGenerator,
    build_deepseek_client_kwargs,
    build_unsplash_client_kwargs,
)

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
            print(chunk, end="", flush=True)

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TMP_DIR / f"{sanitize_filename(generator.html_page.title)}.html"
    output_path.write_text(generator.html_page.html_code, encoding="utf-8")
    print(f"\n[OK] Файл сохранён: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Сгенерировать HTML-страницу по промпту")
    parser.add_argument("prompt", nargs="?", default=DEFAULT_PROMPT)
    args = parser.parse_args()
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            asyncio.run(generate_page(args.prompt))
            return
        except (json.decoder.JSONDecodeError, httpx.HTTPError) as exc:
            print(f"\n[Попытка {attempt}/{MAX_ATTEMPTS}: {exc}]", file=sys.stderr)

    print("\n[ОШИБКА] Генерация не удалась после нескольких попыток.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
