import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse

from page_generator import DEFAULT_PROMPT, SITE_HTML_PATH, stream_site_html
from schemas import (
    CreateSiteRequest,
    GeneratedSitesResponse,
    SiteGenerationRequest,
    SiteResponse,
)

HTML_STUB_PATH = Path(__file__).resolve().parent.parent.parent / "stub" / "index.html"
SCREENSHOT_PATH = Path(__file__).resolve().parent.parent.parent / "stub" / "screenshot.jpg"


_SITES: dict[int, SiteResponse] = {}
_BACKGROUND_TASKS: set[asyncio.Task[None]] = set()


router = APIRouter(prefix="/sites", tags=["Sites"])


def _next_id() -> int:
    return max(_SITES, default=0) + 1


def _run_in_background(coro: Any) -> None:
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)


def build_site(
    request: Request,
    site_id: int,
    *,
    title: str,
    prompt: str,
) -> SiteResponse:
    base = str(request.base_url).rstrip("/")
    now = datetime.now(timezone.utc)
    return SiteResponse(
        id=site_id,
        title=title,
        htmlCodeUrl=f"{base}/frontend-api/sites/{site_id}/html",
        htmlCodeDownloadUrl=f"{base}/frontend-api/sites/{site_id}/html?download=1",
        screenshotUrl=f"{base}/frontend-api/sites/{site_id}/screenshot",
        prompt=prompt,
        createdAt=now,
        updatedAt=now,
    )


def mock_site(request: Request, site_id: int = 1) -> SiteResponse:
    base = str(request.base_url).rstrip("/")
    return SiteResponse(
        id=site_id,
        title="Стегозавры",
        htmlCodeUrl=f"{base}/frontend-api/sites/{site_id}/html",
        htmlCodeDownloadUrl=f"{base}/frontend-api/sites/{site_id}/html?download=1",
        screenshotUrl=f"{base}/frontend-api/sites/{site_id}/screenshot",
        prompt="Сделай сайт про Стегозавров",
        createdAt=datetime(2025, 6, 15, 18, 29, 56, tzinfo=timezone.utc),
        updatedAt=datetime(2025, 6, 15, 18, 29, 56, tzinfo=timezone.utc),
    )


@router.get(
    "/my",
    response_model=GeneratedSitesResponse,
    summary="Получить список сгенерированных сайтов текущего пользователя",
)
def get_user_sites(request: Request) -> GeneratedSitesResponse:
    return GeneratedSitesResponse(sites=[mock_site(request)])


@router.post(
    "/create",
    response_model=SiteResponse,
    summary="Создать сайт",
)
def create_site(
    request: Request,
    create_request: CreateSiteRequest,
) -> SiteResponse:
    site_id = _next_id()
    title = create_request.title or create_request.prompt[:128]
    _SITES[site_id] = build_site(
        request,
        site_id,
        title=title,
        prompt=create_request.prompt,
    )
    return _SITES[site_id]


@router.post(
    "/{site_id}/generate",
    response_class=HTMLResponse,
    summary="Сгенерировать HTML код сайта",
    description="Код сайта будет транслироваться стримом по мере генерации.",
    responses={
        200: {
            "description": "HTML-код сайта, передаётся стримом",
            "content": {
                "text/html": {
                    "schema": {
                        "type": "string",
                        "example": "<!DOCTYPE html><html><body>Стегозавры</body></html>",
                    },
                },
            },
        },
    },
)
async def generate_site(
    site_id: int,
    request: SiteGenerationRequest | None = None,
) -> StreamingResponse:
    prompt = request.prompt if request else DEFAULT_PROMPT
    queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def relay() -> None:
        try:
            async for chunk in stream_site_html(prompt):
                await queue.put(chunk)
            if site_id in _SITES:
                _SITES[site_id] = _SITES[site_id].model_copy(
                    update={"updatedAt": datetime.now(timezone.utc)},
                )
        finally:
            await queue.put(None)

    _run_in_background(relay())

    async def stream() -> AsyncGenerator[str]:
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk

    return StreamingResponse(stream(), media_type="text/html")


@router.get(
    "/{site_id}/html",
    summary="Просмотр HTML кода сайта",
)
def view_site_html(
    request: Request,
    site_id: int,
    download: bool = False,
) -> FileResponse:
    path = SITE_HTML_PATH if SITE_HTML_PATH.exists() else HTML_STUB_PATH
    return FileResponse(
        path,
        media_type="text/html",
        filename="index.html" if download else None,
    )


@router.get(
    "/{site_id}/screenshot",
    summary="Скриншот сайта",
)
def site_screenshot(request: Request, site_id: int) -> FileResponse:
    return FileResponse(SCREENSHOT_PATH, media_type="image/jpeg")


@router.get(
    "/{site_id}",
    response_model=SiteResponse,
    summary="Получить сайт",
    responses={
        404: {
            "description": "Сайт не найден",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"detail": {"type": "string"}},
                        "required": ["detail"],
                    },
                    "example": {"detail": "Site not found"},
                },
            },
        },
    },
)
def get_site(request: Request, site_id: int) -> SiteResponse:
    return _SITES.get(site_id) or mock_site(request, site_id=site_id)
