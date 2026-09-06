from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================================================
    # APPLICATION
    # =========================================================

    app_name: str = "OnboardAI"
    app_env: str = "development"

    # =========================================================
    # AI / GROQ
    # =========================================================

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"

    # =========================================================
    # AUTHENTICATION
    # =========================================================

    auth_secret: str = ""

    # =========================================================
    # QUEUE
    # =========================================================

    queue_autostart: bool = True
    queue_poll_seconds: float = 1.0
    queue_max_attempts: int = 3

    # =========================================================
    # KNOWLEDGE / CHROMA
    # =========================================================

    knowledge_enabled: bool = True
    chroma_persist_dir: str = "./data/chroma"

    # =========================================================
    # OBSERVABILITY
    # =========================================================

    otel_enabled: bool = False
    otel_service_name: str = "onboardai-backend"

    # =========================================================
    # SCREENING
    # =========================================================

    screening_provider: str = "demo"
    screening_api_url: str = ""
    screening_api_key: str = ""

    # =========================================================
    # EMAIL / SMTP
    # =========================================================

    email_enabled: bool = False

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False

    # =========================================================
    # PYDANTIC SETTINGS
    # =========================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()