"""Fail-first tests for deterministic signal payload generation."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from importlib import import_module
from typing import Any, cast

import pytest

BuildDeterministicSignalPayloadCallable = Callable[..., Mapping[str, object]]


def _load_portfolio_ml_service_module() -> object:
    """Load portfolio_ml service module in fail-first mode."""

    try:
        return import_module("app.portfolio_ml.service")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "Fail-first baseline: missing module app.portfolio_ml.service. "
            "Implement tasks 3.1-3.2 before deterministic payload tests can pass.",
        )
        raise AssertionError from exc


def _load_callable(name: str, *, task_hint: str) -> Callable[..., Any]:
    """Load one named callable from portfolio_ml service module."""

    module = _load_portfolio_ml_service_module()
    candidate = getattr(module, name, None)
    if candidate is None:
        pytest.fail(
            f"Fail-first baseline: missing callable {name}(). "
            f"Implement task {task_hint} before this test can pass.",
        )
    return cast(Callable[..., Any], candidate)


def _signal_ids(payload: Mapping[str, object]) -> set[str]:
    """Extract stable signal IDs from one signal payload mapping."""

    rows_obj = payload.get("signals", [])
    if not isinstance(rows_obj, list):
        return set()
    rows = cast(list[object], rows_obj)
    stable_ids: set[str] = set()
    for row_obj in rows:
        if isinstance(row_obj, Mapping):
            row = cast(Mapping[str, object], row_obj)
            signal_id = row.get("signal_id")
            if isinstance(signal_id, str):
                stable_ids.add(signal_id)
    return stable_ids


def test_equivalent_snapshot_inputs_return_identical_signal_payloads() -> None:
    """Equivalent snapshots should return byte-for-byte deterministic signal payload values."""

    build_deterministic_signal_payload = cast(
        BuildDeterministicSignalPayloadCallable,
        _load_callable("build_deterministic_signal_payload", task_hint="3.2"),
    )

    snapshot_payload: dict[str, object] = {
        "scope": "portfolio",
        "snapshot_id": "snap-ledger-2026-04-01",
        "market_snapshot_id": "snap-market-2026-04-01",
        "instrument_symbol": None,
        "series_points": [
            {"captured_at": "2026-03-29T00:00:00Z", "value": "100.0"},
            {"captured_at": "2026-03-30T00:00:00Z", "value": "102.0"},
            {"captured_at": "2026-03-31T00:00:00Z", "value": "101.0"},
            {"captured_at": "2026-04-01T00:00:00Z", "value": "103.0"},
        ],
    }

    first_payload = build_deterministic_signal_payload(snapshot_input=snapshot_payload)
    second_payload = build_deterministic_signal_payload(snapshot_input=snapshot_payload)

    assert first_payload == second_payload


def test_signal_payload_contains_stable_signal_ids_for_v1_contract() -> None:
    """Signal payload should carry stable v1 IDs for deterministic consumer rendering."""

    build_deterministic_signal_payload = cast(
        BuildDeterministicSignalPayloadCallable,
        _load_callable("build_deterministic_signal_payload", task_hint="3.2"),
    )

    payload = build_deterministic_signal_payload(
        snapshot_input={
            "scope": "portfolio",
            "snapshot_id": "snap-ledger-2026-04-01",
            "market_snapshot_id": "snap-market-2026-04-01",
            "series_points": [
                {"captured_at": "2026-03-29T00:00:00Z", "value": "100.0"},
                {"captured_at": "2026-03-30T00:00:00Z", "value": "102.0"},
                {"captured_at": "2026-03-31T00:00:00Z", "value": "101.0"},
                {"captured_at": "2026-04-01T00:00:00Z", "value": "103.0"},
            ],
        },
    )

    stable_ids = _signal_ids(payload)
    assert {
        "trend_30d",
        "momentum_90d",
        "volatility_regime",
        "drawdown_state",
    }.issubset(stable_ids)
