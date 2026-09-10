from datetime import datetime

from pydantic import BaseModel, Field


class UserDetailsResponse(BaseModel):
    email: str = Field(
        description="Email пользователя",
        examples=["example@example.com"],
    )
    isActive: bool = Field(
        description="Активен ли аккаунт",
        examples=[True],
    )
    profileId: int = Field(
        description="Идентификатор профиля",
        examples=[1],
    )
    registeredAt: datetime = Field(
        description="Дата регистрации",
        examples=["2025-06-15T18:29:56+00:00"],
    )
    updatedAt: datetime = Field(
        description="Дата последнего обновления пользователя",
        examples=["2025-06-15T18:29:56+00:00"],
    )
    username: str = Field(
        description="Имя пользователя",
        examples=["user123"],
    )
