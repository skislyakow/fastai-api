from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

SCREENSHOT_FORMAT = Literal["png", "jpeg", "webp"]


class DeepSeekSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_key: SecretStr
    max_connections: PositiveInt | None = None
    timeout: PositiveInt | None = None
    base_url: AnyHttpUrl | None = None
    model: str | None = None


class UnsplashSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_key: SecretStr
    max_connections: PositiveInt | None = None
    timeout: PositiveInt | None = None
    proxy: AnyHttpUrl | None = None


class S3Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_default=True)
    endpoint_url: AnyHttpUrl = AnyHttpUrl("http://localhost:9000")
    access_key_id: SecretStr
    secret_access_key: SecretStr
    bucket_name: str = "fastai-sites"
    region_name: str = "us-east-1"
    connect_timeout: PositiveInt | None = None
    read_timeout: PositiveInt | None = None
    max_pool_connections: PositiveInt | None = None


class GotenbergSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint_url: AnyHttpUrl
    max_connections: PositiveInt = 5
    timeout: PositiveInt = 10
    width: PositiveInt = 1280
    wait_delay: PositiveInt = 8
    default_screenshot_format: SCREENSHOT_FORMAT = "jpeg"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )
    deepseek: DeepSeekSettings
    unsplash: UnsplashSettings
    s3: S3Settings
    gotenberg: GotenbergSettings

    debug: bool = False


settings = Settings()  # type: ignore[reportCallIssue]
