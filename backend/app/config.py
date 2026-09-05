"""
Centralized configuration. All secrets come from environment variables.
NEVER hardcode API keys, DB URLs, or payment credentials here.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"
    secret_key: str = "dev-only-change-me"

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    database_url: str = ""

    # AI provider abstraction
    ai_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    anthropic_api_key: str = ""

    # Razorpay — TEST MODE only in this build
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_mode: str = "test"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_razorpay_configured(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
