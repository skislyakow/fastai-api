from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

from routers.sites import router as sites_router
from schemas import UserDetailsResponse

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(docs_url="/frontend-api/docs")

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
        registeredAt=datetime(2025, 6, 15, 18, 29, 56),
        updatedAt=datetime(2025, 6, 15, 18, 29, 56),
        username="user123",
    )


app.include_router(router, prefix="/frontend-api")
app.include_router(sites_router, prefix="/frontend-api")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
