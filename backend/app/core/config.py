from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "FELAGI-Review"
    service_name: str = "felagi-review"
    environment: str = Field(default="development", alias="FELAGI_APP_ENV")
    debug: bool = Field(default=True, alias="FELAGI_APP_DEBUG")
    api_v1_prefix: str = "/api"
    database_url: str = Field(
        default="postgresql+asyncpg://felagi:felagi@localhost:5432/felagi_review",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    jwt_secret: str = Field(
        default="change-me-in-production", alias="FELAGI_JWT_SECRET"
    )
    jwt_expire_minutes: int = Field(
        default=60 * 24 * 7, alias="FELAGI_JWT_EXPIRE_MINUTES"
    )

    github_client_id: str | None = Field(
        default=None, alias="FELAGI_APP_GITHUB_CLIENT_ID"
    )
    github_client_secret: str | None = Field(
        default=None, alias="FELAGI_APP_GITHUB_CLIENT_SECRET"
    )
    github_redirect_uri: str | None = Field(
        default=None, alias="FELAGI_APP_GITHUB_REDIRECT_URI"
    )
    frontend_url: str = Field(
        default="http://localhost:5173", alias="FELAGI_APP_FRONTEND_URL"
    )
    github_api_base_url: str = "https://api.github.com"
    github_oauth_authorize_url: str = "https://github.com/login/oauth/authorize"
    github_oauth_token_url: str = "https://github.com/login/oauth/access_token"

    ai_provider: str = Field(default="openai", alias="AI_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    ollama_base_url: str = Field(
        default="http://localhost:11434", alias="OLLAMA_BASE_URL"
    )

    encryption_key: str | None = Field(default=None, alias="ENCRYPTION_KEY")
    sentry_dsn: str | None = Field(default=None, alias="SENTRY_DSN")
    frontend_origin: str = Field(
        default="http://localhost:5173", alias="FELAGI_APP_FRONTEND_URL"
    )


settings = Settings()
