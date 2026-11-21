from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "emite-nfse"
    app_version: str = "0.1.0"
    ambiente: str = "producao_restrita"  # producao_restrita | producao

    certificado_pfx_path: Path | None = None
    certificado_senha: str = ""

    ver_aplic: str = "emite-nfse_0.1.0"
    http_timeout_seconds: float = 60.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
