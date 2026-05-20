from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5432/org_structure"
    log_level: str = "INFO"
    app_title: str = "Organization Structure API"
    app_version: str = "1.0.0"


settings = Settings()
