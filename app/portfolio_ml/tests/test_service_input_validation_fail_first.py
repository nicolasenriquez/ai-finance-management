"""Fail-first tests for portfolio_ml service input validation boundaries."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType

import pytest


def _load_service_module() -> ModuleType:
    """Load portfolio_ml service module with fail-first guidance."""

    try:
        return import_module("app.portfolio_ml.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ml.service. "
            "Implement tasks 3.x/4.x service contracts before validation tests can pass.",
        )
        raise AssertionError from exc


@pytest.mark.asyncio
async def test_signal_service_rejects_blank_instrument_symbol_after_trimming() -> None:
    """Instrument scope signal requests should reject whitespace-only symbols."""

    service_module = _load_service_module()
    scope_enum = getattr(service_module, "PortfolioMLScope", None)
    client_error_type = getattr(service_module, "PortfolioMLClientError", None)
    signal_callable = getattr(service_module, "get_portfolio_ml_signal_response", None)

    if scope_enum is None or client_error_type is None or signal_callable is None:
        pytest.fail(
            "Fail-first baseline: missing PortfolioMLScope, PortfolioMLClientError, "
            "or get_portfolio_ml_signal_response in app.portfolio_ml.service.",
        )
    if not isinstance(client_error_type, type) or not issubclass(
        client_error_type, Exception
    ):
        pytest.fail(
            "Fail-first baseline: PortfolioMLClientError must be an Exception subclass."
        )

    with pytest.raises(client_error_type) as exc_info:
        await signal_callable(
            scope=scope_enum.INSTRUMENT_SYMBOL,
            instrument_symbol="   ",
        )

    status_code = getattr(exc_info.value, "status_code", None)
    assert status_code == 422
    assert "instrument_symbol is required" in str(exc_info.value)


@pytest.mark.asyncio
async def test_forecast_service_rejects_blank_instrument_symbol_after_trimming() -> (
    None
):
    """Instrument scope forecast requests should reject whitespace-only symbols."""

    service_module = _load_service_module()
    scope_enum = getattr(service_module, "PortfolioMLScope", None)
    client_error_type = getattr(service_module, "PortfolioMLClientError", None)
    forecast_callable = getattr(
        service_module, "get_portfolio_ml_forecast_response", None
    )

    if scope_enum is None or client_error_type is None or forecast_callable is None:
        pytest.fail(
            "Fail-first baseline: missing PortfolioMLScope, PortfolioMLClientError, "
            "or get_portfolio_ml_forecast_response in app.portfolio_ml.service.",
        )
    if not isinstance(client_error_type, type) or not issubclass(
        client_error_type, Exception
    ):
        pytest.fail(
            "Fail-first baseline: PortfolioMLClientError must be an Exception subclass."
        )

    with pytest.raises(client_error_type) as exc_info:
        await forecast_callable(
            scope=scope_enum.INSTRUMENT_SYMBOL,
            instrument_symbol="   ",
        )

    status_code = getattr(exc_info.value, "status_code", None)
    assert status_code == 422
    assert "instrument_symbol is required" in str(exc_info.value)
