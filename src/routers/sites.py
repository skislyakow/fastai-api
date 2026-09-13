import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, StreamingResponse

from schemas import (
    CreateSiteRequest,
    GeneratedSitesResponse,
    SiteGenerationRequest,
    SiteResponse,
)

HTML_STUB_PATH = Path(__file__).resolve().parent.parent.parent / "stub" / "index.html"
SCREENSHOT_PATH = Path(__file__).resolve().parent.parent.parent / "stub" / "screenshot.jpg"


router = APIRouter(prefix="/sites", tags=["Sites"])


def mock_site(request: Request, site_id: int = 1) -> SiteResponse:
    base = str(request.base_url).rstrip("/")
    return SiteResponse(
        id=site_id,
        title="Стегозавры",
        htmlCodeUrl=f"{base}/frontend-api/sites/{site_id}/html",
        htmlCodeDownloadUrl=f"{base}/frontend-api/sites/{site_id}/html?download=1",
        screenshotUrl=f"{base}/frontend-api/sites/{site_id}/screenshot",
        prompt="Сделай сайт про Стегозавров",
        createdAt=datetime(2025, 6, 15, 18, 29, 56),
        updatedAt=datetime(2025, 6, 15, 18, 29, 56),
    )


async def stream_html_stub():
    html = HTML_STUB_PATH.read_text(encoding="utf-8")
    for i in range(0, len(html), 500):
        yield html[i : i + 500]
        await asyncio.sleep(0.2)


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
def create_site(request: Request, create_request: CreateSiteRequest) -> SiteResponse:
    return mock_site(request)


@router.post(
    "/{site_id}/generate",
    summary="Сгенерировать HTML код сайта",
    description="Код сайта будет транслироваться стримом по мере генерации.",
)
async def generate_site(
    site_id: int,
    request: SiteGenerationRequest,
) -> StreamingResponse:
    return StreamingResponse(stream_html_stub(), media_type="text/html")


@router.get(
    "/{site_id}/html",
    summary="Просмотр HTML кода сайта",
)
def view_site_html(request: Request, site_id: int, download: bool = False) -> FileResponse:
    return FileResponse(
        HTML_STUB_PATH,
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
)
def get_site(request: Request, site_id: int) -> SiteResponse:
    return mock_site(request, site_id=site_id)
