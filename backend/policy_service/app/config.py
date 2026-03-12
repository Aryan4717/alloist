from pydantic_settings import BaseSettings, SettingsConfigDict

from alloist_secrets import get, register_secret_key

# Register keys for log redaction
for _key in (
    "POLICY_SERVICE_API_KEY",
    "JWT_SECRET",
    "EVIDENCE_SIGNING_PRIVATE_KEY",
    "EVIDENCE_SIGNING_PUBLIC_KEY",
    "DATABASE_URL",
):
    register_secret_key(_key)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Non-secret config
    AUDIT_CLEANUP_INTERVAL_SEC: int = 3600
    JWT_ALGORITHM: str = "HS256"
    TOKEN_SERVICE_URL: str = "http://localhost:8000"

    # Secret fields - loaded via secrets.get() on access
    @property
    def DATABASE_URL(self) -> str:
        return get("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/token_service"

    @property
    def POLICY_SERVICE_API_KEY(self) -> str:
        return get("POLICY_SERVICE_API_KEY") or ""

    @property
    def EVIDENCE_SIGNING_PRIVATE_KEY(self) -> str:
        return get("EVIDENCE_SIGNING_PRIVATE_KEY") or ""

    @property
    def EVIDENCE_SIGNING_PUBLIC_KEY(self) -> str:
        return get("EVIDENCE_SIGNING_PUBLIC_KEY") or ""

    @property
    def JWT_SECRET(self) -> str:
        return get("JWT_SECRET") or "change-me-in-production"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
