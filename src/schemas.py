from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints


class UserDetailsResponse(BaseModel):
    email: EmailStr = Field(
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


SiteTitle = Annotated[str, StringConstraints(max_length=128)]


class CreateSiteRequest(BaseModel):
    prompt: str = Field(
        description="Описание сайта для генерации",
        examples=["Стегозавры"],
    )
    title: SiteTitle = Field(
        description="Название сайта",
        examples=["Мой сайт"],
        default="",
    )


class SiteGenerationRequest(BaseModel):
    prompt: str = Field(
        description="Описание сайта для генерации",
        examples=["Стегозавры"],
    )


class SiteResponse(BaseModel):
    id: int = Field(
        description="Идентификатор сайта",
        examples=[1],
    )
    title: str = Field(
        description="Название сайта",
        examples=["Стегозавры"],
    )
    urlPath: str = Field(
        default="",
        description="URL-путь сайта",
        examples=[""],
    )
    htmlCodeUrl: str | None = Field(
        description="Ссылка на html-код сайта",
        examples=["https://google.com"],
    )
    htmlCodeDownloadUrl: str | None = Field(
        description="Ссылка на скачивание HTML-кода сайта",
        examples=["https://google.com"],
    )
    screenshotUrl: str | None = Field(
        description="Ссылка на скриншот сайта",
        examples=["https://google.com"],
    )
    prompt: str = Field(
        description="Описание сайта для генерации",
        examples=["Стегозавры"],
    )
    createdAt: datetime = Field(
        description="Дата создания сайта",
        examples=["2025-06-15T18:29:56+00:00"],
    )
    updatedAt: datetime = Field(
        description="Дата последнего обновления сайта",
        examples=["2025-06-15T18:29:56+00:00"],
    )


class GeneratedSitesResponse(BaseModel):
    sites: list[SiteResponse] = Field(
        description="Список сгенерированных сайтов",
    )
