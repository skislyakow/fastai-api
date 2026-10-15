from datetime import datetime
from typing import Annotated

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
)


class CamelCaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class UserDetailsResponse(CamelCaseModel):
    email: EmailStr = Field(
        description="Email пользователя",
        examples=["example@example.com"],
    )
    is_active: bool = Field(
        serialization_alias="isActive",
        description="Активен ли аккаунт",
        examples=[True],
    )
    profile_id: int = Field(
        serialization_alias="profileId",
        description="Идентификатор профиля",
        examples=[1],
    )
    registered_at: datetime = Field(
        serialization_alias="registeredAt",
        description="Дата регистрации",
        examples=["2025-06-15T18:29:56+00:00"],
    )
    updated_at: datetime = Field(
        serialization_alias="updatedAt",
        description="Дата последнего обновления пользователя",
        examples=["2025-06-15T18:29:56+00:00"],
    )
    username: str = Field(
        description="Имя пользователя",
        examples=["user123"],
    )


SiteTitle = Annotated[str, StringConstraints(max_length=128)]


class CreateSiteRequest(CamelCaseModel):
    prompt: str = Field(
        description="Описание сайта для генерации",
        examples=["Стегозавры"],
    )
    title: SiteTitle = Field(
        description="Название сайта",
        examples=["Мой сайт"],
        default="",
    )


class SiteGenerationRequest(CamelCaseModel):
    prompt: str = Field(
        description="Описание сайта для генерации",
        examples=["Стегозавры"],
    )


class SiteResponse(CamelCaseModel):
    id: int = Field(
        description="Идентификатор сайта",
        examples=[1],
    )
    title: str = Field(
        description="Название сайта",
        examples=["Стегозавры"],
    )
    html_code_url: AnyHttpUrl | None = Field(
        serialization_alias="htmlCodeUrl",
        description="Ссылка на html-код сайта",
        examples=["https://google.com"],
    )
    html_code_download_url: AnyHttpUrl | None = Field(
        serialization_alias="htmlCodeDownloadUrl",
        description="Ссылка на скачивание HTML-кода сайта",
        examples=["https://google.com"],
    )
    screenshot_url: AnyHttpUrl | None = Field(
        serialization_alias="screenshotUrl",
        description="Ссылка на скриншот сайта",
        examples=["https://google.com"],
    )
    prompt: str = Field(
        description="Описание сайта для генерации",
        examples=["Стегозавры"],
    )
    created_at: datetime = Field(
        serialization_alias="createdAt",
        description="Дата создания сайта",
        examples=["2025-06-15T18:29:56+00:00"],
    )
    updated_at: datetime = Field(
        serialization_alias="updatedAt",
        description="Дата последнего обновления сайта",
        examples=["2025-06-15T18:29:56+00:00"],
    )


class GeneratedSitesResponse(CamelCaseModel):
    sites: list[SiteResponse] = Field(
        description="Список сгенерированных сайтов",
    )
