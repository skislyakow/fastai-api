import asyncio
import json
import sys
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path
from typing import Any

import anyio
import anyio.to_thread
import httpx
from html_page_generator import (
    AsyncDeepseekClient,
    AsyncPageGenerator,
    AsyncUnsplashClient,
)
from html_page_generator._html_page_generator import (
    FIND_IMAGES_PROMPT,  # noqa: PLC2701
    GENERATE_HTML_PROMPT,  # noqa: PLC2701
    REGENERATE_HTML_PROMPT,  # noqa: PLC2701
    HtmlPage,  # noqa: PLC2701
    get_images_from_unsplash,  # noqa: PLC2701
)
from langchain_core.messages import ToolMessage
from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode, create_react_agent

from env_settings import settings

SITE_HTML_PATH = Path(__file__).resolve().parent.parent / "index.html"
DEFAULT_PROMPT = (
    "Личная страница fullstack Python-разработчика. Современный дизайн, тёмная тема, "
    "плавные анимации заголовков и параллакс-фон. Секции: вверху имя и роль с фото и "
    "приветствием, «Обо мне» с блоком навыков (Python, FastAPI, Django, PostgreSQL, "
    "SQLAlchemy, Docker, Git, JavaScript), «Проекты» — карточки с примерами работ и "
    "ссылками, «Услуги» — что я делаю (бэкенд, API, автоматизация, деплой), внизу "
    "секция контактов с формой и ссылками на Telegram/GitHub. Используй изображения "
    "в тематике программирования и технологий. Адаптивная вёрстка, чтобы сайт хорошо "
    "выглядел и на телефоне."
)
MAX_ATTEMPTS = 3


def _echo(chunk: str) -> None:
    if settings.debug:
        print(chunk, end="", flush=True)


async def ainvoke_with_retry(
    agent: Any,
    message: dict[str, str],
    *,
    temperature: float,
    config: Any,
) -> dict[str, Any]:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return await agent.ainvoke(
                input={"messages": [message], "temperature": temperature},
                config=config,
            )
        except (json.decoder.JSONDecodeError, httpx.HTTPError) as exc:
            print(
                f"[Попытка {attempt}/{MAX_ATTEMPTS}: {exc}]",
                file=sys.stderr,
            )
    raise RuntimeError(f"Генерация не удалась после {MAX_ATTEMPTS} попыток.")


def build_deepseek_client_kwargs() -> dict[str, str]:
    kwargs: dict[str, str] = {}
    if settings.deepseek.base_url:
        kwargs["deepseek_base_url"] = settings.deepseek.base_url
    if settings.deepseek.model:
        kwargs["deepseek_model"] = settings.deepseek.model
    return kwargs


def build_unsplash_client_kwargs() -> dict[str, str]:
    kwargs: dict[str, str] = {}
    if settings.unsplash.proxy:
        kwargs["proxy"] = settings.unsplash.proxy
    return kwargs


class StreamPageGenerator(AsyncPageGenerator):
    def __init__(self, *, debug_mode: bool = False) -> None:
        client = AsyncDeepseekClient.get_initialized_instance()
        model = ChatDeepSeek(
            model=client.deepseek_model,
            api_key=client.deepseek_api_key,
            http_async_client=client,
            api_base=client.deepseek_base_url,  # type: ignore[reportCallIssue]
            max_tokens=32768,
            temperature=0.7,
        )
        self.html_page = HtmlPage()
        self.current_year = datetime.now().year
        self.agent = create_react_agent(
            model,
            tools=ToolNode([get_images_from_unsplash]),
            checkpointer=InMemorySaver(),
            debug=debug_mode,
        )
        self.config = {"configurable": {"thread_id": uuid.uuid4().hex}}

    async def search_images(self, user_prompt: str) -> AsyncGenerator[str]:
        message = {
            "role": "user",
            "content": FIND_IMAGES_PROMPT.format(user_prompt=user_prompt),
        }
        response = await self.agent.ainvoke(
            input={"messages": [message], "temperature": 0.1},
            config=self.config,
        )
        for msg in response["messages"]:
            if isinstance(msg, ToolMessage) and msg.content:
                yield f"{msg.content}\n"

    async def generate_html(self, user_prompt: str) -> AsyncGenerator[str]:
        message = {
            "role": "user",
            "content": GENERATE_HTML_PROMPT.format(
                user_prompt=user_prompt,
                current_year=self.current_year,
            ),
        }
        response = await ainvoke_with_retry(
            self.agent,
            message,
            temperature=2,
            config=self.config,
        )
        html_code = response["messages"][-1].content
        self.html_page.html_code = html_code
        for i in range(0, len(html_code), 4000):
            yield html_code[i : i + 4000]
            await asyncio.sleep(0.2)

    async def regenerate_html(self) -> AsyncGenerator[str]:
        message = {"role": "user", "content": REGENERATE_HTML_PROMPT}
        response = await ainvoke_with_retry(
            self.agent,
            message,
            temperature=2,
            config=self.config,
        )
        html_code = response["messages"][-1].content
        self.html_page.html_code = html_code
        for i in range(0, len(html_code), 4000):
            yield html_code[i : i + 4000]
            await asyncio.sleep(0.2)


async def save_generated_site(generator: StreamPageGenerator) -> None:
    if generator.html_page.html_code:
        with anyio.CancelScope(shield=True):
            await anyio.to_thread.run_sync(
                SITE_HTML_PATH.write_text,
                generator.html_page.html_code,
                "utf-8",
            )


async def stream_site_html(prompt: str) -> AsyncGenerator[str]:
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
        try:
            async for chunk in generator.generate_html(prompt):
                _echo(chunk)
                yield chunk
            await generator.check_html()
            if not generator.html_page.is_valid:
                async for chunk in generator.regenerate_html():
                    _echo(chunk)
                    yield chunk
        except Exception as exc:
            print(f"[ОШИБКА ГЕНЕРАЦИИ] {exc}", file=sys.stderr)
            if not generator.html_page.html_code:
                yield f"<!DOCTYPE html><html><body><h1>Не удалось сгенерировать страницу</h1><p>{exc}</p></body></html>"
        finally:
            await save_generated_site(generator)
