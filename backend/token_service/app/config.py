from pydantic_settings import BaseSettings, SettingsConfigDict

from alloist_secrets import get, register_secret_key

# Register keys for log redaction
for _key in (
    "TOKEN_SERVICE_API_KEY",
    "JWT_SECRET",
    "REVOCATION_SIGNING_PRIVATE_KEY",
    "REVOCATION_SIGNING_PUBLIC_KEY",
    "GOOGLE_CLIENT_SECRET",
    "GITHUB_CLIENT_SECRET",
    "DATABASE_URL",
):
    register_secret_key(_key)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Non-secret config (from env/pydantic)
    REDIS_URL: str = "redis://localhost:6379/0"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    GITHUB_CLIENT_ID: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/auth/github/callback"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_SECONDS: int = 3600
    AUTH_CALLBACK_URL: str = "http://localhost:3000/auth/callback"

    # Secret fields - loaded via secrets.get() on access
    @property
    def DATABASE_URL(self) -> str:
        return get("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/token_service"

    @property
    def TOKEN_SERVICE_API_KEY(self) -> str:
        return get("TOKEN_SERVICE_API_KEY") or ""

    @property
    def REVOCATION_SIGNING_PRIVATE_KEY(self) -> str:
        return get("REVOCATION_SIGNING_PRIVATE_KEY") or ""

    @property
    def REVOCATION_SIGNING_PUBLIC_KEY(self) -> str:
        return get("REVOCATION_SIGNING_PUBLIC_KEY") or ""

    @property
    def GOOGLE_CLIENT_SECRET(self) -> str:
        return get("GOOGLE_CLIENT_SECRET") or ""

    @property
    def GITHUB_CLIENT_SECRET(self) -> str:
        return get("GITHUB_CLIENT_SECRET") or ""

    @property
    def JWT_SECRET(self) -> str:
        return get("JWT_SECRET") or "change-me-in-production"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
