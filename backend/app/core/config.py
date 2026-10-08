from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    adzuna_app_id: str | None = None
    adzuna_app_key: str | None = None

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    embedding_api_url: str | None = None
    embedding_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    embedding_timeout_seconds: float = 30.0

    # Optional LLM optimization provider. Resume generation remains
    # deterministic when these values are unset.
    resume_llm_api_url: str | None = None
    resume_llm_api_key: str | None = None
    resume_llm_model: str = "gpt-4o-mini"
    resume_llm_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
