from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from env_settings import settings
from logging_config import get_logger, setup_logging
from routers.sites import router as sites_router
from routers.users import router as users_router
from s3_client import create_s3_client, ensure_bucket

logger = get_logger(__name__)
STATIC_DIR = Path(__file__).parent / "static"

setup_logging(debug=settings.debug)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with create_s3_client() as s3:
        await ensure_bucket(s3, settings.s3.bucket_name)
        app.state.s3 = s3
        yield


app = FastAPI(docs_url="/frontend-api/docs", lifespan=lifespan)

app.include_router(users_router, prefix="/frontend-api")
app.include_router(sites_router, prefix="/frontend-api")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

logger.info(settings.model_dump_json(indent=4))
