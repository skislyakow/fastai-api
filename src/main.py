from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(docs_url="/frontend-api/docs")

router = APIRouter(tags=["Users"])


@router.get("/users/me")
def get_current_user():
    return {
        "email": "example@example.com",
        "isActive": True,
        "profileId": "1",
        "registeredAt": "2025-06-15T18:29:56+00:00",
        "updatedAt": "2025-06-15T18:29:56+00:00",
        "username": "user123",
    }


app.include_router(router, prefix="/frontend-api")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
