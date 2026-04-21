"""Tests for app.core.config module."""

import os
from unittest.mock import patch

from app.core.config import Settings, get_settings


def create_settings() -> Settings:
    """Create Settings instance for testing.

    Helper function for creating Settings in tests. pydantic-settings loads
    required fields from environment variables at runtime. Mypy's static analysis
    doesn't understand this and expects constructor arguments. This is a known
    limitation with pydantic-settings, so we suppress the call-arg error.

    Returns:
        Settings instance loaded from environment variables.
    """
    return Settings()  # type: ignore[call-arg]


def test_settings_defaults() -> None:
    """Test Settings instantiation with default values."""
    with patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
            "LOG_LEVEL": "INFO",  # Override .env file to test default value
        },
    ):
        settings = create_settings()

        assert settings.app_name == "AI Finance Management"
        assert settings.version == "0.1.0"
        assert settings.environment == "development"
        assert settings.log_level == "INFO"
        assert settings.api_prefix == "/api"
        assert settings.pdf_preflight_min_text_chars == 20
        assert settings.pdf_upload_storage_root == ".data/pdf_uploads"
        assert settings.pdf_upload_max_bytes == 10 * 1024 * 1024
        assert settings.pdf_upload_max_pages == 50
        assert settings.market_data_yfinance_period == "5y"
        assert settings.market_data_yfinance_interval == "1d"
        assert settings.market_data_yfinance_timeout_seconds == 30.0
        assert settings.market_data_yfinance_max_retries == 1
        assert settings.market_data_yfinance_retry_backoff_seconds == 0.5
        assert settings.market_data_yfinance_request_spacing_seconds == 1.0
        assert settings.market_data_yfinance_history_fallback_periods == [
            "3y",
            "1y",
            "6mo",
        ]
        assert settings.market_data_yfinance_default_currency == "USD"
        assert settings.market_data_yfinance_auto_adjust is False
        assert settings.market_data_yfinance_repair is False
        assert (
            settings.market_data_symbol_universe_path
            == "app/market_data/symbol_universe.v1.json"
        )
        assert "http://localhost:3000" in settings.allowed_origins
        assert "http://localhost:8123" in settings.allowed_origins


def test_settings_from_environment() -> None:
    """Test Settings can be overridden by environment variables."""
    with patch.dict(
        os.environ,
        {
            "APP_NAME": "Test App",
            "VERSION": "1.0.0",
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "DEBUG",
            "API_PREFIX": "/v1",
            "PDF_PREFLIGHT_MIN_TEXT_CHARS": "35",
            "PDF_UPLOAD_STORAGE_ROOT": ".data/custom_uploads",
            "PDF_UPLOAD_MAX_BYTES": "2048",
            "PDF_UPLOAD_MAX_PAGES": "5",
            "MARKET_DATA_YFINANCE_PERIOD": "1y",
            "MARKET_DATA_YFINANCE_INTERVAL": "1d",
            "MARKET_DATA_YFINANCE_TIMEOUT_SECONDS": "12.5",
            "MARKET_DATA_YFINANCE_MAX_RETRIES": "3",
            "MARKET_DATA_YFINANCE_RETRY_BACKOFF_SECONDS": "1.25",
            "MARKET_DATA_YFINANCE_REQUEST_SPACING_SECONDS": "0.75",
            "MARKET_DATA_YFINANCE_HISTORY_FALLBACK_PERIODS": '["6mo","3mo","1mo"]',
            "MARKET_DATA_YFINANCE_DEFAULT_CURRENCY": "cad",
            "MARKET_DATA_YFINANCE_AUTO_ADJUST": "false",
            "MARKET_DATA_YFINANCE_REPAIR": "false",
            "MARKET_DATA_SYMBOL_UNIVERSE_PATH": "app/market_data/custom_symbol_universe.json",
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
        },
    ):
        settings = create_settings()

        assert settings.app_name == "Test App"
        assert settings.version == "1.0.0"
        assert settings.environment == "production"
        assert settings.log_level == "DEBUG"
        assert settings.api_prefix == "/v1"
        assert settings.pdf_preflight_min_text_chars == 35
        assert settings.pdf_upload_storage_root == ".data/custom_uploads"
        assert settings.pdf_upload_max_bytes == 2048
        assert settings.pdf_upload_max_pages == 5
        assert settings.market_data_yfinance_period == "1y"
        assert settings.market_data_yfinance_interval == "1d"
        assert settings.market_data_yfinance_timeout_seconds == 12.5
        assert settings.market_data_yfinance_max_retries == 3
        assert settings.market_data_yfinance_retry_backoff_seconds == 1.25
        assert settings.market_data_yfinance_request_spacing_seconds == 0.75
        assert settings.market_data_yfinance_history_fallback_periods == [
            "6mo",
            "3mo",
            "1mo",
        ]
        assert settings.market_data_yfinance_default_currency == "cad"
        assert settings.market_data_yfinance_auto_adjust is False
        assert settings.market_data_yfinance_repair is False
        assert (
            settings.market_data_symbol_universe_path
            == "app/market_data/custom_symbol_universe.json"
        )


def test_allowed_origins_parsing() -> None:
    """Test allowed_origins parsing from environment variable.

    Note: pydantic-settings expects JSON array format for list fields.
    """
    with patch.dict(
        os.environ,
        {
            "ALLOWED_ORIGINS": '["http://example.com","http://localhost:3000","http://test.com"]',
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
        },
    ):
        settings = create_settings()

        assert len(settings.allowed_origins) == 3
        assert "http://example.com" in settings.allowed_origins
        assert "http://localhost:3000" in settings.allowed_origins
        assert "http://test.com" in settings.allowed_origins


def test_get_settings_caching() -> None:
    """Test get_settings() returns cached instance."""
    # Clear the cache first
    get_settings.cache_clear()

    settings1 = get_settings()
    settings2 = get_settings()

    # Should return the same instance (cached)
    assert settings1 is settings2


def test_settings_case_insensitive() -> None:
    """Test settings are case-insensitive."""
    with patch.dict(
        os.environ,
        {
            "app_name": "Lower Case App",
            "ENVIRONMENT": "PRODUCTION",
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
        },
    ):
        settings = create_settings()

        assert settings.app_name == "Lower Case App"
        assert settings.environment == "PRODUCTION"


def test_portfolio_ai_copilot_model_allowlist_parses_json() -> None:
    """Test copilot allowlist accepts JSON array string."""
    with patch.dict(
        os.environ,
        {
            "PORTFOLIO_AI_COPILOT_MODEL_ALLOWLIST": '["openai/gpt-oss-20b","llama-3.1-8b-instant"]',
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
        },
    ):
        settings = create_settings()

        assert settings.portfolio_ai_copilot_model_allowlist == [
            "openai/gpt-oss-20b",
            "llama-3.1-8b-instant",
        ]


def test_portfolio_ai_copilot_model_allowlist_parses_csv() -> None:
    """Test copilot allowlist accepts CSV string."""
    with patch.dict(
        os.environ,
        {
            "PORTFOLIO_AI_COPILOT_MODEL_ALLOWLIST": "openai/gpt-oss-20b, llama-3.1-8b-instant",
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
        },
    ):
        settings = create_settings()

        assert settings.portfolio_ai_copilot_model_allowlist == [
            "openai/gpt-oss-20b",
            "llama-3.1-8b-instant",
        ]
