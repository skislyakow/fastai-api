from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from html_page_generator import AsyncDeepseekClient, AsyncUnsplashClient

from env_settings import settings
from logging_config import get_logger, setup_logging
from page_generator import build_deepseek_client_kwargs, build_unsplash_client_kwargs
from routers.sites import cancel_background_tasks, router as sites_router
from routers.users import router as users_router
from s3_client import create_s3_client, ensure_bucket

logger = get_logger(__name__)
STATIC_DIR = Path(__file__).parent / "static"

setup_logging(debug=settings.debug)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with AsyncExitStack() as stack:
        s3 = await stack.enter_async_context(create_s3_client())
        await ensure_bucket(s3, settings.s3.bucket_name)
        app.state.s3 = s3

        await stack.enter_async_context(
            AsyncUnsplashClient.setup(
                settings.unsplash.api_key.get_secret_value(),
                timeout=settings.unsplash.timeout,
                **build_unsplash_client_kwargs(),
            ),
        )
        app.state.unsplash = AsyncUnsplashClient.get_initialized_instance()

        await stack.enter_async_context(
            AsyncDeepseekClient.setup(
                settings.deepseek.api_key.get_secret_value(),
                timeout=settings.deepseek.timeout,
                **build_deepseek_client_kwargs(),
            ),
        )
        app.state.deepseek = AsyncDeepseekClient.get_initialized_instance()

        app.state.gotenberg = await stack.enter_async_context(
            httpx.AsyncClient(
                base_url=str(settings.gotenberg.endpoint_url),
                timeout=settings.gotenberg.timeout,
                limits=httpx.Limits(max_connections=settings.gotenberg.max_connections),
            ),
        )
        try:
            yield
        finally:
            await cancel_background_tasks()


app = FastAPI(docs_url="/frontend-api/docs", lifespan=lifespan)

app.include_router(users_router, prefix="/frontend-api")
app.include_router(sites_router, prefix="/frontend-api")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

logger.info(settings.model_dump_json(indent=4))
