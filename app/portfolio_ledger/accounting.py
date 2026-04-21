"""Dataset-1 v1 accounting-policy constants and typed policy schema."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from enum import StrEnum

from pydantic import BaseModel

from app.portfolio_ledger.schemas import LedgerEventType


class AccountingPolicyVersion(StrEnum):
    """Version identifiers for explicitly frozen accounting policies."""

    DATASET_1_V1 = "dataset_1_v1"


class LotMatchingMethod(StrEnum):
    """Supported lot-matching methods for sell-side processing."""

    FIFO = "fifo"


class UnsupportedAccountingConcern(StrEnum):
    """Accounting concerns explicitly unsupported in dataset-1 v1."""

    FEE_ADJUSTMENT = "fee_adjustment"
    FX_ADJUSTMENT = "fx_adjustment"
    UNSUPPORTED_CORPORATE_ACTION = "unsupported_corporate_action"


class AccountingPolicyConfig(BaseModel):
    """Typed configuration for one frozen accounting policy definition."""

    version: AccountingPolicyVersion
    lot_matching_method: LotMatchingMethod
    buy_cost_basis_field: str
    sell_proceeds_field: str
    dividends_change_lot_basis: bool
    splits_realize_gain: bool
    infer_fee_adjustments: bool
    infer_fx_adjustments: bool
    supported_event_types: tuple[LedgerEventType, ...]
    unsupported_concerns: tuple[UnsupportedAccountingConcern, ...]


DATASET_1_V1_ACCOUNTING_POLICY = AccountingPolicyConfig(
    version=AccountingPolicyVersion.DATASET_1_V1,
    lot_matching_method=LotMatchingMethod.FIFO,
    buy_cost_basis_field="aporte_usd",
    sell_proceeds_field="rescate_usd",
    dividends_change_lot_basis=False,
    splits_realize_gain=False,
    infer_fee_adjustments=False,
    infer_fx_adjustments=False,
    supported_event_types=(
        LedgerEventType.TRADE,
        LedgerEventType.DIVIDEND,
        LedgerEventType.SPLIT,
    ),
    unsupported_concerns=(
        UnsupportedAccountingConcern.FEE_ADJUSTMENT,
        UnsupportedAccountingConcern.FX_ADJUSTMENT,
        UnsupportedAccountingConcern.UNSUPPORTED_CORPORATE_ACTION,
    ),
)

_QTY_SCALE = Decimal("0.000000001")
_MONEY_SCALE = Decimal("0.01")
_UNIT_COST_BASIS_SCALE = Decimal("0.000000001")


def match_sell_trade_fifo(
    *,
    open_lots: Sequence[Mapping[str, object]],
    sell_trade: Mapping[str, object],
) -> dict[str, object]:
    """Match a sell trade against open lots in FIFO order."""

    sold_qty = _coerce_positive_decimal(
        sell_trade.get("sold_qty"),
        field="sold_qty",
    )
    remaining_to_match = sold_qty
    total_matched_basis_usd = Decimal("0")
    dispositions: list[dict[str, str]] = []

    for lot in open_lots:
        if remaining_to_match <= Decimal("0"):
            break

        lot_remaining_qty = _coerce_non_negative_decimal(
            lot.get("remaining_qty"),
            field="remaining_qty",
        )
        if lot_remaining_qty == Decimal("0"):
            continue

        lot_id = _coerce_non_empty_str(
            lot.get("lot_id"),
            field="lot_id",
        )
        lot_unit_cost_basis_usd = _coerce_non_negative_decimal(
            lot.get("unit_cost_basis_usd"),
            field="unit_cost_basis_usd",
        )

        matched_qty = min(remaining_to_match, lot_remaining_qty)
        matched_cost_basis_usd = (matched_qty * lot_unit_cost_basis_usd).quantize(
            _MONEY_SCALE,
            rounding=ROUND_HALF_UP,
        )

        dispositions.append(
            {
                "lot_id": lot_id,
                "matched_qty": _format_decimal(
                    value=matched_qty,
                    scale=_QTY_SCALE,
                ),
                "matched_cost_basis_usd": _format_decimal(
                    value=matched_cost_basis_usd,
                    scale=_MONEY_SCALE,
                ),
            }
        )
        total_matched_basis_usd += matched_cost_basis_usd
        remaining_to_match -= matched_qty

    if remaining_to_match > Decimal("0"):
        raise ValueError(
            "Insufficient open lot quantity for FIFO sell matching: "
            f"sold_qty={sold_qty}, unmatched_qty={remaining_to_match}."
        )

    return {
        "dispositions": dispositions,
        "total_matched_basis_usd": _format_decimal(
            value=total_matched_basis_usd,
            scale=_MONEY_SCALE,
        ),
    }


def calculate_realized_gain_from_fifo(
    *,
    dispositions: Sequence[Mapping[str, object]],
    sell_trade: Mapping[str, object],
) -> Decimal:
    """Calculate realized gain using sell proceeds minus FIFO-matched basis."""

    proceeds_usd = _coerce_decimal(
        sell_trade.get("proceeds_usd"),
        field="proceeds_usd",
    )
    matched_basis_usd = sum(
        (
            _coerce_decimal(
                disposition.get("matched_cost_basis_usd"),
                field="matched_cost_basis_usd",
            )
            for disposition in dispositions
        ),
        start=Decimal("0"),
    )
    return (proceeds_usd - matched_basis_usd).quantize(
        _MONEY_SCALE,
        rounding=ROUND_HALF_UP,
    )


def apply_split_to_open_lots(
    *,
    open_lots: Sequence[Mapping[str, object]],
    split_event: Mapping[str, object],
) -> list[dict[str, str]]:
    """Apply split ratio to open lots while preserving total lot basis."""

    split_ratio_value = _coerce_positive_decimal(
        split_event.get("split_ratio_value"),
        field="split_ratio_value",
    )
    adjusted_lots: list[dict[str, str]] = []

    for lot in open_lots:
        lot_id = _coerce_non_empty_str(
            lot.get("lot_id"),
            field="lot_id",
        )
        remaining_qty = _coerce_non_negative_decimal(
            lot.get("remaining_qty"),
            field="remaining_qty",
        )
        total_cost_basis_usd = _coerce_non_negative_decimal(
            lot.get("total_cost_basis_usd"),
            field="total_cost_basis_usd",
        )

        adjusted_remaining_qty = (remaining_qty * split_ratio_value).quantize(
            _QTY_SCALE,
            rounding=ROUND_HALF_UP,
        )
        if adjusted_remaining_qty <= Decimal("0"):
            raise ValueError(
                "Split-adjusted remaining quantity must be positive: "
                f"lot_id={lot_id}, adjusted_remaining_qty={adjusted_remaining_qty}."
            )

        adjusted_unit_cost_basis_usd = (
            total_cost_basis_usd / adjusted_remaining_qty
        ).quantize(
            _UNIT_COST_BASIS_SCALE,
            rounding=ROUND_HALF_UP,
        )

        adjusted_lots.append(
            {
                "lot_id": lot_id,
                "remaining_qty": _format_decimal(
                    value=adjusted_remaining_qty,
                    scale=_QTY_SCALE,
                ),
                "total_cost_basis_usd": _format_decimal(
                    value=total_cost_basis_usd,
                    scale=_MONEY_SCALE,
                ),
                "unit_cost_basis_usd": _format_decimal(
                    value=adjusted_unit_cost_basis_usd,
                    scale=_UNIT_COST_BASIS_SCALE,
                ),
            }
        )

    return adjusted_lots


def _coerce_decimal(value: object, *, field: str) -> Decimal:
    """Coerce one scalar input to Decimal for accounting math."""

    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric; bool is not allowed.")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError(f"{field} must be numeric and non-empty.")
        try:
            return Decimal(normalized_value)
        except InvalidOperation as exc:
            raise ValueError(f"{field} must be a valid decimal string.") from exc
    raise ValueError(f"{field} must be numeric.")


def _coerce_non_negative_decimal(value: object, *, field: str) -> Decimal:
    """Coerce one decimal value and enforce non-negative constraints."""

    coerced_value = _coerce_decimal(value, field=field)
    if coerced_value < Decimal("0"):
        raise ValueError(f"{field} must be greater than or equal to zero.")
    return coerced_value


def _coerce_positive_decimal(value: object, *, field: str) -> Decimal:
    """Coerce one decimal value and enforce positive constraints."""

    coerced_value = _coerce_decimal(value, field=field)
    if coerced_value <= Decimal("0"):
        raise ValueError(f"{field} must be greater than zero.")
    return coerced_value


def _coerce_non_empty_str(value: object, *, field: str) -> str:
    """Coerce one value to a non-empty string."""

    if not isinstance(value, str):
        raise ValueError(f"{field} must be a non-empty string.")
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"{field} must be a non-empty string.")
    return normalized_value


def _format_decimal(*, value: Decimal, scale: Decimal) -> str:
    """Format a decimal value using fixed-point deterministic scale."""

    return format(value.quantize(scale, rounding=ROUND_HALF_UP), "f")
