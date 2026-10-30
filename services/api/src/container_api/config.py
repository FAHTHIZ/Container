# SPDX-License-Identifier: Apache-2.0
"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEVELOPMENT_SECRET = "container-development-secret-change-before-deploy"


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    app_name: str = "Container API"
    app_version: str = "0.3.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./container.db"
    jwt_secret: str = _DEVELOPMENT_SECRET
    access_token_ttl_minutes: int = 30
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    worker_poll_seconds: float = 1.0
    artifacts_path: Path = Path("./artifacts")
    max_artifact_bytes: int = 100 * 1024 * 1024
    inference_base_url: str = ""
    inference_api_key: str = ""
    inference_model: str = ""
    inference_timeout_seconds: float = 90.0

    model_config = SettingsConfigDict(
        env_prefix="CONTAINER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def validate_runtime(self) -> None:
        """Reject unsafe placeholder secrets and invalid upload limits in production."""
        if self.max_artifact_bytes < 1:
            raise RuntimeError("CONTAINER_MAX_ARTIFACT_BYTES must be positive.")
        if self.environment.lower() in {"production", "prod"}:
            if self.jwt_secret == _DEVELOPMENT_SECRET or len(self.jwt_secret) < 32:
                raise RuntimeError(
                    "CONTAINER_JWT_SECRET must be unique and at least 32 characters in production."
                )


settings = Settings()
