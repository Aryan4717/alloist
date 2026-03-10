from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/token_service"
    POLICY_SERVICE_API_KEY: str = ""
    EVIDENCE_SIGNING_PRIVATE_KEY: str = ""
    EVIDENCE_SIGNING_PUBLIC_KEY: str = ""
    AUDIT_CLEANUP_INTERVAL_SEC: int = 3600
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
