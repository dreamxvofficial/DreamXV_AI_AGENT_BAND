"""
DreamXV AI Studio — Centralized Configuration
==============================================
Loads all environment variables and exposes a typed settings object.
Uses pydantic-settings for validation and type coercion.
"""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

# NOTE: Do NOT force VERCEL=1 here — this breaks local /tmp path usage on Windows.
# Vercel serverless sets this env var automatically in its runtime.

from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field

# ---------------------------------------------------------------------------
# Load .env from project root (one level above /backend)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


class Settings(BaseSettings):
    """
    Validated configuration for all AI providers and application settings.
    Values are loaded from environment variables (and .env file).
    """

    # --- Featherless AI (Primary LLM) ---
    featherless_api_key: str = Field(
        default="your_key_here",
        description="Featherless AI API key",
    )
    featherless_base_url: str = Field(
        default="https://api.featherless.ai/v1",
        description="Featherless AI base URL",
    )
    featherless_model: str = Field(
        default="Qwen/Qwen2.5-14B-Instruct",
        description="Default Featherless model identifier",
    )

    # --- AIMLAPI (Fallback LLM + Image Generation) ---
    aiml_api_key: str = Field(
        default="your_key_here",
        description="AIMLAPI key",
    )
    aiml_base_url: str = Field(
        default="https://api.aimlapi.com/v1",
        description="AIMLAPI base URL",
    )
    aiml_model: str = Field(
        default="qwen-plus",
        description="Default AIMLAPI model identifier",
    )
    aiml_image_model: str = Field(
        default="flux/schnell",
        description="AIMLAPI image generation model",
    )

    # --- Band SDK (Multi-Agent Rooms) ---
    band_api_key: str = Field(
        default="your_key_here",
        description="Band SDK / Thenvoi API key",
    )
    band_base_url: str = Field(
        default="https://api.band.ai",
        description="Band SDK base URL",
    )

    # --- Application Paths ---
    project_root: Path = _PROJECT_ROOT
    outputs_dir: Path = _PROJECT_ROOT / "outputs"
    images_dir: Path = _PROJECT_ROOT / "outputs" / "images"
    prompts_dir: Path = Path(__file__).resolve().parent / "prompts"

    # --- Server ---
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: list[str] = ["*"]

    # --- LLM Defaults ---
    default_temperature: float = 0.7
    default_max_tokens: int = 4096

    class Config:
        env_file = str(_ENV_PATH)
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **values):
        super().__init__(**values)
        # Dynamically redirect directories to /tmp under Vercel Serverless
        if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            self.outputs_dir = Path("/tmp/outputs")
            self.images_dir = Path("/tmp/outputs/images")


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
