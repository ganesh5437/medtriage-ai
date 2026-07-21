"""
config.py — central settings for MedTriage AI.
All env vars are read here ONCE. Rest of the app imports `settings`
from this file instead of touching os.environ directly.
"""
import os
from functools import lru_cache


class Settings:
    # --- LLM ---
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")  # mock | anthropic | openai
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # --- Database ---
    # Leave DATABASE_URL blank -> falls back to local SQLite file (zero setup)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "") or "sqlite:///./medtriage.db"

    # --- Vector DB ---
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "medtriage")

    # --- Auth ---
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-only-change-this-secret")
    JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

    # --- Session retention (gap-fix #2) ---
    SESSION_TTL_HOURS: int = int(os.getenv("SESSION_TTL_HOURS", "24"))

    # --- Rate limiting (gap-fix #1) ---
    RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))
    MAX_TURNS_PER_SESSION: int = int(os.getenv("MAX_TURNS_PER_SESSION", "30"))

    # --- File upload (gap-fix #3) ---
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "5"))

    # --- CORS (gap-fix: prod CORS) ---
    # comma-separated list, e.g. "http://localhost:5173,https://medtriage-ai.vercel.app"
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")

    # --- App ---
    APP_ENV: str = os.getenv("APP_ENV", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    APP_VERSION: str = "0.1.0"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
