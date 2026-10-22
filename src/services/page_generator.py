import uuid
from collections.abc import AsyncGenerator, Callable
from pathlib import Path
from typing import Any

import anyio
import anyio.to_thread
from html_page_generator import (
    AsyncDeepseekClient,
    AsyncPageGenerator,
)
from html_page_generator._html_page_generator import get_images_from_unsplash
from langchain_core.messages import AIMessageChunk
from langchain_core.runnables import RunnableConfig
from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode, create_react_agent

from config.env_settings import DeepSeekSettings, UnsplashSettings
from config.logging_config import get_logger

logger = get_logger(__name__)

SITE_HTML_PATH = Path(__file__).resolve().parent.parent.parent / "index.html"
MAX_ATTEMPTS = 3


def _log_chunk(chunk: str, *, debug: bool) -> None:
    if debug:
        logger.debug("%s", chunk)


async def _stream_with_retry(
    generator: AsyncPageGenerator,
    stream_factory: Callable[[], AsyncGenerator[str]],
    *,
    debug: bool,
) -> AsyncGenerator[str]:
    last_exc: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if attempt > 1:
            generator.config.setdefault("configurable", {})["thread_id"] = uuid.uuid4().hex
        emitted = False
        try:
            async for chunk in stream_factory():
                if not chunk:
                    continue
                emitted = True
                _log_chunk(chunk, debug=debug)
                yield chunk
            return
        except Exception as exc:  # noqa: BLE001
            if emitted:
                raise
            last_exc = exc
            logger.warning("Попытка %s/%s: %s", attempt, MAX_ATTEMPTS, exc)
    raise RuntimeError(f"Генерация не удалась после {MAX_ATTEMPTS} попыток.") from last_exc


def build_deepseek_client_kwargs(deepseek_settings: DeepSeekSettings) -> dict[str, str]:
    kwargs: dict[str, str] = {}
    if deepseek_settings.base_url:
        kwargs["deepseek_base_url"] = str(deepseek_settings.base_url)
    if deepseek_settings.model:
        kwargs["deepseek_model"] = deepseek_settings.model
    return kwargs


def build_unsplash_client_kwargs(unsplash_settings: UnsplashSettings) -> dict[str, str]:
    kwargs: dict[str, str] = {}
    if unsplash_settings.proxy:
        kwargs["proxy"] = str(unsplash_settings.proxy)
    return kwargs


class AssistantOnlyAgent:
    def __init__(self, agent: Any) -> None:
        self._agent = agent

    async def astream(
        self,
        *,
        config: RunnableConfig,
        **kwargs: Any,
    ) -> AsyncGenerator[tuple[AIMessageChunk, dict[str, Any]]]:
        async for message, metadata in self._agent.astream(config=config, **kwargs):
            if isinstance(message, AIMessageChunk):
                yield message, metadata

    async def ainvoke(self, *, config: RunnableConfig, **kwargs: Any) -> Any:
        return await self._agent.ainvoke(config=config, **kwargs)


class ConfiguredPageGenerator(AsyncPageGenerator):
    def __init__(self, *, debug_mode: bool = False) -> None:
        super().__init__(debug_mode=debug_mode)
        client = AsyncDeepseekClient.get_initialized_instance()
        model = ChatDeepSeek.model_validate(
            {
                "model": client.deepseek_model,
                "api_key": client.deepseek_api_key,
                "http_async_client": client,
                "base_url": client.deepseek_base_url,
                "max_tokens": 32768,
                "temperature": 0.7,
            },
        )
        self.agent: Any = AssistantOnlyAgent(
            create_react_agent(
                model,
                tools=ToolNode([get_images_from_unsplash]),
                checkpointer=InMemorySaver(),
                debug=debug_mode,
            ),
        )


async def save_generated_site(generator: AsyncPageGenerator) -> None:
    if generator.html_page.html_code:
        with anyio.CancelScope(shield=True):
            await anyio.to_thread.run_sync(
                SITE_HTML_PATH.write_text,
                generator.html_page.html_code,
                "utf-8",
            )


async def remove_generated_site() -> None:
    if SITE_HTML_PATH.exists():
        await anyio.to_thread.run_sync(SITE_HTML_PATH.unlink)


async def _stream_html(
    generator: AsyncPageGenerator,
    prompt: str,
    *,
    debug: bool,
) -> AsyncGenerator[str]:
    async for chunk in _stream_with_retry(
        generator,
        lambda: generator.generate_html(prompt),
        debug=debug,
    ):
        yield chunk
    await generator.check_html()
    if not generator.html_page.is_valid:
        async for chunk in _stream_with_retry(generator, generator.regenerate_html, debug=debug):
            yield chunk


async def stream_site_html(prompt: str, *, debug: bool) -> AsyncGenerator[str]:
    await remove_generated_site()
    generator = ConfiguredPageGenerator(debug_mode=debug)
    emitted = False
    try:
        async for chunk in _stream_html(generator, prompt, debug=debug):
            emitted = True
            yield chunk
    except Exception as exc:
        logger.error("ОШИБКА ГЕНЕРАЦИИ: %s", exc)
        if not emitted:
            yield f"<!DOCTYPE html><html><body><h1>Не удалось сгенерировать страницу</h1><p>{exc}</p></body></html>"
    finally:
        await save_generated_site(generator)
