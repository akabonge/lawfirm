from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5-20251001"
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    chroma_path: str = "./chroma_db"
    db_path: str = "./lawfirm.db"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
