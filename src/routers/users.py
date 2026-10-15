from datetime import UTC, datetime

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
        is_active=True,
        profile_id=1,
        registered_at=datetime(2025, 6, 15, 18, 29, 56, tzinfo=UTC),
        updated_at=datetime(2025, 6, 15, 18, 29, 56, tzinfo=UTC),
        username="user123",
    )
