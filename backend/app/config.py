from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ReviewHub"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api"
    database_url: str = "postgresql+asyncpg://reviewhub:reviewhub@localhost:5432/reviewhub"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7

    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_redirect_uri: str | None = None
    github_api_base_url: str = "https://api.github.com"
    github_oauth_authorize_url: str = "https://github.com/login/oauth/authorize"
    github_oauth_token_url: str = "https://github.com/login/oauth/access_token"

    ai_provider: str = "openai"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    encryption_key: str | None = None
    sentry_dsn: str | None = None
    frontend_origin: str = "http://localhost:5173"


settings = Settings()
