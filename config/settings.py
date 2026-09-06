from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OnboardAI"
    app_env: str = "development"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    auth_secret: str = ""
    queue_autostart: bool = True
    queue_poll_seconds: float = 1.0
    queue_max_attempts: int = 3
    knowledge_enabled: bool = True
    chroma_persist_dir: str = "./data/chroma"
    otel_enabled: bool = False
    otel_service_name: str = "onboardai-backend"
    screening_provider: str = "demo"
    screening_api_url: str = ""
    screening_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
