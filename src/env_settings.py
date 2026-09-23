from pydantic import BaseModel, ConfigDict, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )
    deepseek: DeepSeekSettings
    unsplash: UnsplashSettings
    debug: bool = False
    s3: S3Settings


settings = Settings()  # type: ignore[reportCallIssue]
