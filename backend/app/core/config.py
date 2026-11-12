import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "Agente de Gestión Ciudadana - Alcaldía de Barranquilla"
    APP_ENV: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # IA Providers (Groq Cloud + Ollama Local $0)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    LLM_MODEL: str = "qwen2.5:0.5b"
    LLM_FALLBACK_MODEL: str = "llama3:latest"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data_barranquilla.db'}"
    SNOWFLAKE_READY: bool = True
    SNOWFLAKE_ACCOUNT: str = ""
    SNOWFLAKE_USER: str = ""
    SNOWFLAKE_PASSWORD: str = ""
    SNOWFLAKE_DATABASE: str = "BARRANQUILLA_CITIZEN_DB"
    SNOWFLAKE_SCHEMA: str = "OPERATIONS"
    SNOWFLAKE_WAREHOUSE: str = "COMPUTE_WH"

    # Parameters
    MAX_RAG_RESULTS: int = 4
    CONFIDENCE_THRESHOLD: float = 0.70
    SANDBOX_MODE: bool = True

    class Config:
        env_file = str(BASE_DIR / ".env")
        extra = "ignore"

settings = Settings()
