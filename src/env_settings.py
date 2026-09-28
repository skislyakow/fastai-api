from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

SCREENSHOT_FORMAT = Literal["png", "jpeg", "webp"]


class DeepSeekSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_key: SecretStr
    max_connections: int | None = Field(default=None, gt=0)
    timeout: int | None = Field(default=None, gt=0)
    base_url: str | None = None
    model: str | None = None


class UnsplashSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_key: SecretStr
    max_connections: int | None = Field(default=None, gt=0)
    timeout: int | None = Field(default=None, gt=0)
    proxy: str | None = None


class S3Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint_url: str = "http://localhost:9000"
    access_key_id: SecretStr
    secret_access_key: SecretStr
    bucket_name: str = "fastai-sites"
    region_name: str = "us-east-1"
    connect_timeout: int | None = Field(default=None, gt=0)
    read_timeout: int | None = Field(default=None, gt=0)
    max_pool_connections: int | None = Field(default=None, gt=0)


class GotenbergSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint_url: str
    max_connections: int = Field(default=5, gt=0)
    timeout: int = Field(default=10, gt=0)
    width: int = Field(default=1280, gt=0)
    wait_delay: int = Field(default=8, gt=0)
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
