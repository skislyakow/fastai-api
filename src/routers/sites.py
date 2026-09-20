from datetime import datetime, timezone
from pathlib import Path

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
def create_site(request: Request, create_request: CreateSiteRequest) -> SiteResponse:
    return mock_site(request)


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
    return StreamingResponse(stream_site_html(prompt), media_type="text/html")


@router.get(
    "/{site_id}/html",
    summary="Просмотр HTML кода сайта",
)
def view_site_html(request: Request, site_id: int, download: bool = False) -> FileResponse:
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
    return mock_site(request, site_id=site_id)
