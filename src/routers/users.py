from datetime import datetime, timezone

from fastapi import APIRouter

from schemas import UserDetailsResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
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
