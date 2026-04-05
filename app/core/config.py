"""Application configuration using pydantic-settings.

This module provides centralized configuration management:
- Environment variable loading from .env file
- Type-safe settings with validation
- Cached settings instance with @lru_cache
- Settings for application, CORS, and future database configuration
"""

import json
from collections.abc import Sequence
from functools import lru_cache
from typing import Annotated, cast

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration.

    All settings can be overridden via environment variables.
    Environment variables are case-insensitive.
    Settings are loaded from .env file if present.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Don't fail if .env file doesn't exist
        extra="ignore",
    )

    # Application metadata
    app_name: str = "AI Finance Management"
    version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"

    # Database
    database_url: str

    # CORS settings
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8123"]

    # PDF preflight
    pdf_preflight_min_text_chars: int = 20

    # PDF ingestion
    pdf_upload_storage_root: str = ".data/pdf_uploads"
    pdf_upload_max_bytes: int = 10 * 1024 * 1024
    pdf_upload_max_pages: int = 50

    # YFinance provider adapter (market-data first slice)
    market_data_yfinance_period: str = "5y"
    market_data_yfinance_interval: str = "1d"
    market_data_yfinance_timeout_seconds: float = Field(default=30.0, gt=0.0)
    market_data_yfinance_max_retries: int = Field(default=1, ge=0, le=5)
    market_data_yfinance_retry_backoff_seconds: float = Field(default=0.5, ge=0.0, le=60.0)
    market_data_yfinance_request_spacing_seconds: float = Field(
        default=1.0,
        ge=0.0,
        le=60.0,
    )
    market_data_yfinance_history_fallback_periods: list[str] = Field(
        default_factory=lambda: ["3y", "1y", "6mo"],
        min_length=1,
        max_length=10,
    )
    market_data_yfinance_default_currency: str = Field(default="USD", min_length=3, max_length=8)
    market_data_yfinance_auto_adjust: bool = False
    market_data_yfinance_repair: bool = False
    market_data_symbol_universe_path: str = "app/market_data/symbol_universe.v1.json"

    # QuantStats reporting
    quant_report_storage_root: str = ".data/quant_reports"
    quant_report_retention_minutes: int = Field(default=60, ge=1, le=1440)

    # Portfolio AI copilot (Groq adapter)
    groq_api_key: str | None = None
    portfolio_ai_copilot_model: str | None = None
    portfolio_ai_copilot_model_allowlist: Annotated[list[str], NoDecode] = Field(
        default_factory=list
    )
    portfolio_ai_copilot_timeout_seconds: float = Field(default=20.0, gt=0.0, le=120.0)
    portfolio_ai_copilot_max_retries: int = Field(default=1, ge=0, le=5)
    portfolio_ai_copilot_groq_base_url: str = "https://api.groq.com"

    @field_validator("portfolio_ai_copilot_model_allowlist", mode="before")
    @classmethod
    def parse_portfolio_ai_copilot_model_allowlist(cls, value: object) -> object:
        """Parse copilot model allowlist from JSON array or CSV-style string."""
        if value is None:
            return []
        if isinstance(value, Sequence) and not isinstance(value, str):
            sequence_items = list(cast(Sequence[object], value))
            parsed_items: list[str] = []
            for item in sequence_items:
                if isinstance(item, str):
                    normalized_item = item.strip()
                else:
                    normalized_item = str(item).strip()
                if normalized_item:
                    parsed_items.append(normalized_item)
            return parsed_items
        if isinstance(value, str):
            normalized = value.strip()
            if normalized == "":
                return []
            if normalized.startswith("["):
                parsed: object = json.loads(normalized)
                if not isinstance(parsed, list):
                    raise ValueError("Expected JSON array for model allowlist.")
                parsed_json_items = cast(list[object], parsed)
                parsed_items_from_json: list[str] = []
                for item in parsed_json_items:
                    if isinstance(item, str):
                        normalized_item = item.strip()
                    else:
                        normalized_item = str(item).strip()
                    if normalized_item:
                        parsed_items_from_json.append(normalized_item)
                return parsed_items_from_json
            return [item.strip() for item in normalized.split(",") if item.strip()]
        raise ValueError("Unsupported model allowlist format.")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    The @lru_cache decorator ensures settings are only loaded once
    and reused across the application lifecycle.

    Returns:
        The application settings instance.
    """
    # pydantic-settings automatically loads required fields (like database_url)
    # from environment variables at runtime. Mypy's static analysis doesn't understand
    # this behavior and expects all required fields as constructor arguments. This is
    # a known limitation of mypy with pydantic-settings. The call-arg error is suppressed
    # as the runtime behavior is correct and type-safe.
    return Settings()  # type: ignore[call-arg]
