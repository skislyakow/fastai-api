import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse

from config.env_settings import Settings
from schemas import (
    CreateSiteRequest,
    GeneratedSitesResponse,
    SiteGenerationRequest,
    SiteResponse,
)
from services.background import run_in_background
from services.generation import relay_html, stream_queue
from services.page_generator import SITE_HTML_PATH
from services.sites import SITES, build_site, create_mock_site, get_next_id

HTML_STUB_PATH = Path(__file__).resolve().parent.parent.parent / "stub" / "index.html"
SCREENSHOT_PATH = Path(__file__).resolve().parent.parent.parent / "stub" / "screenshot.jpg"


router = APIRouter(prefix="/sites", tags=["Sites"])


@router.get(
    "/my",
    response_model=GeneratedSitesResponse,
    summary="Получить список сгенерированных сайтов текущего пользователя",
)
def get_user_sites() -> GeneratedSitesResponse:
    sites = sorted(SITES.values(), key=lambda s: s.id)
    return GeneratedSitesResponse(sites=sites)


@router.post(
    "/create",
    response_model=SiteResponse,
    summary="Создать сайт",
)
def create_site(
    create_request: CreateSiteRequest,
    request: Request,
) -> SiteResponse:
    app_settings: Settings = request.app.state.settings
    site_id = get_next_id()
    title = create_request.title or create_request.prompt[:128]
    SITES[site_id] = build_site(
        site_id,
        title=title,
        prompt=create_request.prompt,
        s3_settings=app_settings.s3,
        screenshot_format=app_settings.gotenberg.default_screenshot_format,
    )
    return SITES[site_id]


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
    request: Request,
    payload: SiteGenerationRequest,
) -> StreamingResponse:
    prompt = payload.prompt
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    app_settings: Settings = request.app.state.settings
    run_in_background(
        relay_html(
            queue,
            prompt=prompt,
            s3=request.app.state.s3,
            gotenberg=request.app.state.gotenberg,
            app_settings=app_settings,
            site_id=site_id,
        ),
    )
    return StreamingResponse(stream_queue(queue), media_type="text/html")


@router.get(
    "/{site_id}/html",
    summary="Просмотр HTML кода сайта",
)
def view_site_html(site_id: int, download: bool = False) -> FileResponse:
    if site_id not in SITES:
        raise HTTPException(status_code=404, detail="Site not found")
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
def get_site_screenshot(site_id: int) -> FileResponse:
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
def get_site(site_id: int, request: Request) -> SiteResponse:
    app_settings: Settings = request.app.state.settings
    return SITES.get(site_id) or create_mock_site(
        site_id=site_id,
        s3_settings=app_settings.s3,
        screenshot_format=app_settings.gotenberg.default_screenshot_format,
    )
