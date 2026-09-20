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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )
    deepseek: DeepSeekSettings
    unsplash: UnsplashSettings
    debug: bool = False


settings = Settings()  # type: ignore[reportCallIssue]
