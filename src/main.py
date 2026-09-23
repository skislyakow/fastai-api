from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aioboto3
from botocore.config import Config
from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

from env_settings import settings
from routers.sites import router as sites_router
from s3_client import ensure_bucket
from schemas import UserDetailsResponse

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    session = aioboto3.Session()
    config_kwargs: dict[str, Any] = {"signature_version": "s3v4"}
    for src, dst in (
        (settings.s3.connect_timeout, "connect_timeout"),
        (settings.s3.read_timeout, "read_timeout"),
        (settings.s3.max_pool_connections, "max_pool_connections"),
    ):
        if src is not None:
            config_kwargs[dst] = src

    s3_cm: Any = session.client(
        "s3",
        endpoint_url=settings.s3.endpoint_url,
        aws_access_key_id=settings.s3.access_key_id.get_secret_value(),
        aws_secret_access_key=settings.s3.secret_access_key.get_secret_value(),
        region_name=settings.s3.region_name,
        config=Config(**config_kwargs),
    )
    async with s3_cm as s3:
        await ensure_bucket(s3, settings.s3.bucket_name)
        app.state.s3 = s3
        yield


app = FastAPI(docs_url="/frontend-api/docs", lifespan=lifespan)

router = APIRouter(tags=["Users"])


@router.get(
    "/users/me",
    response_model=UserDetailsResponse,
    summary="Получить учетные данные пользователя",
)
def get_current_user() -> UserDetailsResponse:
    return UserDetailsResponse(
        email="example@example.com",
        isActive=True,
        profileId=1,
        registeredAt=datetime(2025, 6, 15, 18, 29, 56, tzinfo=timezone.utc),
        updatedAt=datetime(2025, 6, 15, 18, 29, 56, tzinfo=timezone.utc),
        username="user123",
    )


app.include_router(router, prefix="/frontend-api")
app.include_router(sites_router, prefix="/frontend-api")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

print(settings.model_dump_json(indent=4))
