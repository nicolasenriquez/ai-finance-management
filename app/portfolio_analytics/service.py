"""Service helpers for read-only portfolio analytics from ledger truth."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import cast

from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.portfolio_analytics.schemas import (
    PortfolioLotDetailResponse,
    PortfolioLotDetailRow,
    PortfolioSummaryResponse,
    PortfolioSummaryRow,
)
from app.portfolio_ledger.models import DividendEvent, Lot, LotDisposition, PortfolioTransaction
from app.shared.models import utcnow

logger = get_logger(__name__)

_QTY_SCALE = Decimal("0.000000001")
_MONEY_SCALE = Decimal("0.01")


class PortfolioAnalyticsClientError(ValueError):
    """Raised when analytics requests are invalid or unsafe to process."""

    status_code: int

    def __init__(self, message: str, *, status_code: int) -> None:
        """Initialize a client-facing analytics error."""

        super().__init__(message)
        self.status_code = status_code


async def get_portfolio_summary_response(*, db: AsyncSession) -> PortfolioSummaryResponse:
    """Return grouped portfolio summary computed from persisted ledger truth."""

    logger.info("portfolio_analytics.summary_started")
    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            lots_result = await db.execute(select(Lot))
            lot_dispositions_result = await db.execute(select(LotDisposition))
            sell_transactions_result = await db.execute(
                select(PortfolioTransaction).where(
                    func.lower(PortfolioTransaction.trade_side) == "sell",
                )
            )
            dividend_events_result = await db.execute(select(DividendEvent))

            rows_payload = build_grouped_portfolio_summary_from_ledger(
                lots=[_serialize_lot_row(row) for row in lots_result.scalars().all()],
                lot_dispositions=[
                    _serialize_lot_disposition_row(row)
                    for row in lot_dispositions_result.scalars().all()
                ],
                portfolio_transactions=[
                    _serialize_portfolio_transaction_row(row)
                    for row in sell_transactions_result.scalars().all()
                ],
                dividend_events=[
                    _serialize_dividend_event_row(row)
                    for row in dividend_events_result.scalars().all()
                ],
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            summary_response = PortfolioSummaryResponse(
                as_of_ledger_at=as_of_ledger_at,
                rows=[
                    PortfolioSummaryRow.model_validate(row_payload) for row_payload in rows_payload
                ],
            )
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.summary_failed",
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build portfolio summary from ledger due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.summary_completed",
        as_of_ledger_at=summary_response.as_of_ledger_at.isoformat(),
        row_count=len(summary_response.rows),
    )
    return summary_response


async def get_portfolio_lot_detail_response(
    *,
    instrument_symbol: str,
    db: AsyncSession,
) -> PortfolioLotDetailResponse:
    """Return lot-detail analytics for one instrument symbol from persisted ledger truth."""

    normalized_symbol = _normalize_symbol(symbol_value=instrument_symbol, field="instrument_symbol")
    logger.info("portfolio_analytics.lot_detail_started", instrument_symbol=normalized_symbol)

    try:
        async with db.begin():
            await _set_repeatable_read_snapshot(db=db)
            lots_result = await db.execute(
                select(Lot).where(func.upper(Lot.instrument_symbol) == normalized_symbol),
            )
            lots = lots_result.scalars().all()
            lot_ids = [lot.id for lot in lots]

            if not lot_ids:
                logger.info(
                    "portfolio_analytics.lot_detail_rejected",
                    instrument_symbol=normalized_symbol,
                    status_code=404,
                    error="Instrument symbol not found in portfolio ledger.",
                )
                raise PortfolioAnalyticsClientError(
                    f"Instrument symbol '{normalized_symbol}' was not found in the portfolio ledger.",
                    status_code=404,
                )

            lot_dispositions_result = await db.execute(
                select(LotDisposition).where(LotDisposition.lot_id.in_(lot_ids)),
            )
            lot_dispositions = lot_dispositions_result.scalars().all()
            sell_transaction_ids = sorted(
                {disposition.sell_transaction_id for disposition in lot_dispositions}
            )
            sell_transactions: list[PortfolioTransaction] = []
            if sell_transaction_ids:
                sell_transactions_result = await db.execute(
                    select(PortfolioTransaction).where(
                        PortfolioTransaction.id.in_(sell_transaction_ids)
                    ),
                )
                sell_transactions = list(sell_transactions_result.scalars().all())

            detail_payload = build_lot_detail_from_ledger(
                instrument_symbol=normalized_symbol,
                lots=[_serialize_lot_row(row) for row in lots],
                lot_dispositions=[_serialize_lot_disposition_row(row) for row in lot_dispositions],
                portfolio_transactions=[
                    _serialize_portfolio_transaction_row(row) for row in sell_transactions
                ],
            )
            as_of_ledger_at = await _fetch_as_of_ledger_at(db=db)
            lot_detail_response = PortfolioLotDetailResponse(
                as_of_ledger_at=as_of_ledger_at,
                instrument_symbol=cast(str, detail_payload["instrument_symbol"]),
                lots=[
                    PortfolioLotDetailRow.model_validate(lot_payload)
                    for lot_payload in cast(list[dict[str, object]], detail_payload["lots"])
                ],
            )
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_analytics.lot_detail_failed",
            instrument_symbol=normalized_symbol,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioAnalyticsClientError(
            "Failed to build lot detail from ledger due to a database error.",
            status_code=500,
        ) from exc

    logger.info(
        "portfolio_analytics.lot_detail_completed",
        instrument_symbol=lot_detail_response.instrument_symbol,
        as_of_ledger_at=lot_detail_response.as_of_ledger_at.isoformat(),
        lot_count=len(lot_detail_response.lots),
    )
    return lot_detail_response


def build_grouped_portfolio_summary_from_ledger(
    *,
    lots: Sequence[Mapping[str, object]],
    lot_dispositions: Sequence[Mapping[str, object]],
    portfolio_transactions: Sequence[Mapping[str, object]],
    dividend_events: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Compute grouped ledger-only KPI rows by instrument symbol."""

    open_quantity_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    open_cost_basis_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    open_lot_count_by_symbol: dict[str, int] = defaultdict(int)
    lot_id_to_symbol: dict[int, str] = {}

    for lot in lots:
        lot_context = "lot"
        lot_id = _coerce_positive_int(
            value=_read_required_field(record=lot, field="id", context=lot_context),
            field="id",
            context=lot_context,
        )
        symbol = _normalize_symbol(
            symbol_value=_read_required_field(
                record=lot,
                field="instrument_symbol",
                context=lot_context,
            ),
            field="instrument_symbol",
        )
        lot_id_to_symbol[lot_id] = symbol
        remaining_qty = _coerce_decimal(
            value=_read_required_field(record=lot, field="remaining_qty", context=lot_context),
            field="remaining_qty",
            context=lot_context,
        )
        total_cost_basis_usd = _coerce_decimal(
            value=_read_required_field(
                record=lot, field="total_cost_basis_usd", context=lot_context
            ),
            field="total_cost_basis_usd",
            context=lot_context,
        )

        if remaining_qty > Decimal("0"):
            open_quantity_by_symbol[symbol] += remaining_qty
            open_cost_basis_by_symbol[symbol] += total_cost_basis_usd
            open_lot_count_by_symbol[symbol] += 1

    realized_cost_basis_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    disposition_sell_ids_by_symbol: dict[str, set[int]] = defaultdict(set)

    for disposition in lot_dispositions:
        disposition_context = "lot_disposition"
        lot_id = _coerce_positive_int(
            value=_read_required_field(
                record=disposition, field="lot_id", context=disposition_context
            ),
            field="lot_id",
            context=disposition_context,
        )
        symbol_from_lot = lot_id_to_symbol.get(lot_id)
        if symbol_from_lot is None:
            raw_symbol = disposition.get("instrument_symbol")
            if raw_symbol is None:
                raise PortfolioAnalyticsClientError(
                    "Disposition row cannot be resolved to an instrument symbol.",
                    status_code=422,
                )
            symbol = _normalize_symbol(symbol_value=raw_symbol, field="instrument_symbol")
        else:
            symbol = symbol_from_lot

        matched_cost_basis_usd = _coerce_decimal(
            value=_read_required_field(
                record=disposition,
                field="matched_cost_basis_usd",
                context=disposition_context,
            ),
            field="matched_cost_basis_usd",
            context=disposition_context,
        )
        sell_transaction_id = _coerce_positive_int(
            value=_read_required_field(
                record=disposition,
                field="sell_transaction_id",
                context=disposition_context,
            ),
            field="sell_transaction_id",
            context=disposition_context,
        )

        realized_cost_basis_by_symbol[symbol] += matched_cost_basis_usd
        disposition_sell_ids_by_symbol[symbol].add(sell_transaction_id)

    sell_proceeds_by_symbol_and_tx: dict[tuple[str, int], Decimal] = {}
    sell_transaction_ids_by_symbol: dict[str, set[int]] = defaultdict(set)

    for transaction in portfolio_transactions:
        transaction_context = "portfolio_transaction"
        trade_side_raw = _read_required_field(
            record=transaction,
            field="trade_side",
            context=transaction_context,
        )
        if not isinstance(trade_side_raw, str):
            raise PortfolioAnalyticsClientError(
                "Portfolio transaction trade_side must be a string.",
                status_code=422,
            )
        if trade_side_raw.strip().lower() != "sell":
            continue

        symbol = _normalize_symbol(
            symbol_value=_read_required_field(
                record=transaction,
                field="instrument_symbol",
                context=transaction_context,
            ),
            field="instrument_symbol",
        )
        transaction_id = _coerce_positive_int(
            value=_read_required_field(record=transaction, field="id", context=transaction_context),
            field="id",
            context=transaction_context,
        )
        gross_amount_usd = _coerce_decimal(
            value=_read_required_field(
                record=transaction,
                field="gross_amount_usd",
                context=transaction_context,
            ),
            field="gross_amount_usd",
            context=transaction_context,
        )

        key = (symbol, transaction_id)
        previous_amount = sell_proceeds_by_symbol_and_tx.get(key)
        if previous_amount is not None and previous_amount != gross_amount_usd:
            raise PortfolioAnalyticsClientError(
                "Sell transaction gross amount is inconsistent for the same transaction id.",
                status_code=422,
            )
        sell_proceeds_by_symbol_and_tx[key] = gross_amount_usd
        sell_transaction_ids_by_symbol[symbol].add(transaction_id)

    dividend_gross_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    dividend_taxes_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    dividend_net_by_symbol: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for dividend in dividend_events:
        dividend_context = "dividend_event"
        symbol = _normalize_symbol(
            symbol_value=_read_required_field(
                record=dividend,
                field="instrument_symbol",
                context=dividend_context,
            ),
            field="instrument_symbol",
        )
        gross_amount_usd = _coerce_decimal(
            value=_read_required_field(
                record=dividend,
                field="gross_amount_usd",
                context=dividend_context,
            ),
            field="gross_amount_usd",
            context=dividend_context,
        )
        taxes_withheld_usd = _coerce_decimal(
            value=_read_required_field(
                record=dividend,
                field="taxes_withheld_usd",
                context=dividend_context,
            ),
            field="taxes_withheld_usd",
            context=dividend_context,
        )
        net_amount_usd = _coerce_decimal(
            value=_read_required_field(
                record=dividend, field="net_amount_usd", context=dividend_context
            ),
            field="net_amount_usd",
            context=dividend_context,
        )

        dividend_gross_by_symbol[symbol] += gross_amount_usd
        dividend_taxes_by_symbol[symbol] += taxes_withheld_usd
        dividend_net_by_symbol[symbol] += net_amount_usd

    active_symbols = sorted(
        {
            *open_quantity_by_symbol.keys(),
            *realized_cost_basis_by_symbol.keys(),
            *sell_transaction_ids_by_symbol.keys(),
            *dividend_gross_by_symbol.keys(),
            *dividend_taxes_by_symbol.keys(),
            *dividend_net_by_symbol.keys(),
        }
    )

    summary_rows: list[dict[str, object]] = []
    for symbol in active_symbols:
        open_quantity = _quantize_qty(open_quantity_by_symbol.get(symbol, Decimal("0")))
        open_cost_basis_usd = _quantize_money(open_cost_basis_by_symbol.get(symbol, Decimal("0")))
        open_lot_count = open_lot_count_by_symbol.get(symbol, 0)

        realized_proceeds_usd = _quantize_money(
            sum(
                (
                    sell_proceeds_by_symbol_and_tx[(symbol, sell_transaction_id)]
                    for sell_transaction_id in sell_transaction_ids_by_symbol.get(symbol, set())
                    if (symbol, sell_transaction_id) in sell_proceeds_by_symbol_and_tx
                ),
                start=Decimal("0"),
            )
        )
        realized_cost_basis_usd = _quantize_money(
            realized_cost_basis_by_symbol.get(symbol, Decimal("0")),
        )
        realized_gain_usd = _quantize_money(realized_proceeds_usd - realized_cost_basis_usd)

        dividend_gross_usd = _quantize_money(dividend_gross_by_symbol.get(symbol, Decimal("0")))
        dividend_taxes_usd = _quantize_money(dividend_taxes_by_symbol.get(symbol, Decimal("0")))
        dividend_net_usd = _quantize_money(dividend_net_by_symbol.get(symbol, Decimal("0")))

        has_activity = any(
            (
                open_quantity > Decimal("0"),
                realized_proceeds_usd > Decimal("0"),
                realized_cost_basis_usd > Decimal("0"),
                dividend_gross_usd > Decimal("0"),
                dividend_taxes_usd > Decimal("0"),
                dividend_net_usd > Decimal("0"),
            )
        )
        if not has_activity:
            continue

        summary_rows.append(
            {
                "instrument_symbol": symbol,
                "open_quantity": open_quantity,
                "open_cost_basis_usd": open_cost_basis_usd,
                "open_lot_count": open_lot_count,
                "realized_proceeds_usd": realized_proceeds_usd,
                "realized_cost_basis_usd": realized_cost_basis_usd,
                "realized_gain_usd": realized_gain_usd,
                "dividend_gross_usd": dividend_gross_usd,
                "dividend_taxes_usd": dividend_taxes_usd,
                "dividend_net_usd": dividend_net_usd,
            }
        )

    return summary_rows


def build_lot_detail_from_ledger(
    *,
    instrument_symbol: str,
    lots: Sequence[Mapping[str, object]],
    lot_dispositions: Sequence[Mapping[str, object]],
    portfolio_transactions: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Compute lot-detail payload for one normalized instrument symbol."""

    normalized_symbol = _normalize_symbol(
        symbol_value=instrument_symbol,
        field="instrument_symbol",
    )

    selected_lots: list[dict[str, object]] = []
    for lot in lots:
        lot_context = "lot"
        lot_symbol = _normalize_symbol(
            symbol_value=_read_required_field(
                record=lot,
                field="instrument_symbol",
                context=lot_context,
            ),
            field="instrument_symbol",
        )
        if lot_symbol != normalized_symbol:
            continue

        lot_id = _coerce_positive_int(
            value=_read_required_field(record=lot, field="id", context=lot_context),
            field="id",
            context=lot_context,
        )
        selected_lots.append(
            {
                "lot_id": lot_id,
                "opened_on": _coerce_date(
                    value=_read_required_field(record=lot, field="opened_on", context=lot_context),
                    field="opened_on",
                    context=lot_context,
                ),
                "original_qty": _quantize_qty(
                    _coerce_decimal(
                        value=_read_required_field(
                            record=lot,
                            field="original_qty",
                            context=lot_context,
                        ),
                        field="original_qty",
                        context=lot_context,
                    )
                ),
                "remaining_qty": _quantize_qty(
                    _coerce_decimal(
                        value=_read_required_field(
                            record=lot,
                            field="remaining_qty",
                            context=lot_context,
                        ),
                        field="remaining_qty",
                        context=lot_context,
                    )
                ),
                "total_cost_basis_usd": _quantize_money(
                    _coerce_decimal(
                        value=_read_required_field(
                            record=lot,
                            field="total_cost_basis_usd",
                            context=lot_context,
                        ),
                        field="total_cost_basis_usd",
                        context=lot_context,
                    )
                ),
                "unit_cost_basis_usd": _quantize_qty(
                    _coerce_decimal(
                        value=_read_required_field(
                            record=lot,
                            field="unit_cost_basis_usd",
                            context=lot_context,
                        ),
                        field="unit_cost_basis_usd",
                        context=lot_context,
                    )
                ),
                "dispositions": [],
            }
        )

    if not selected_lots:
        raise PortfolioAnalyticsClientError(
            f"Instrument symbol '{normalized_symbol}' was not found in the portfolio ledger.",
            status_code=404,
        )

    lots_by_id = {cast(int, lot_payload["lot_id"]): lot_payload for lot_payload in selected_lots}
    sell_gross_amount_by_transaction_id: dict[int, Decimal] = {}
    for transaction in portfolio_transactions:
        transaction_context = "portfolio_transaction"
        transaction_id = _coerce_positive_int(
            value=_read_required_field(record=transaction, field="id", context=transaction_context),
            field="id",
            context=transaction_context,
        )
        gross_amount_usd = _quantize_money(
            _coerce_decimal(
                value=_read_required_field(
                    record=transaction,
                    field="gross_amount_usd",
                    context=transaction_context,
                ),
                field="gross_amount_usd",
                context=transaction_context,
            )
        )
        sell_gross_amount_by_transaction_id[transaction_id] = gross_amount_usd

    for disposition in lot_dispositions:
        disposition_context = "lot_disposition"
        lot_id = _coerce_positive_int(
            value=_read_required_field(
                record=disposition, field="lot_id", context=disposition_context
            ),
            field="lot_id",
            context=disposition_context,
        )
        lot_payload = lots_by_id.get(lot_id)
        if lot_payload is None:
            continue

        sell_transaction_id = _coerce_positive_int(
            value=_read_required_field(
                record=disposition,
                field="sell_transaction_id",
                context=disposition_context,
            ),
            field="sell_transaction_id",
            context=disposition_context,
        )
        sell_gross_amount_usd = sell_gross_amount_by_transaction_id.get(sell_transaction_id)
        if sell_gross_amount_usd is None:
            raise PortfolioAnalyticsClientError(
                "Lot disposition references a sell transaction that is missing from ledger input.",
                status_code=422,
            )

        disposition_payload: dict[str, object] = {
            "sell_transaction_id": sell_transaction_id,
            "disposition_date": _coerce_date(
                value=_read_required_field(
                    record=disposition,
                    field="disposition_date",
                    context=disposition_context,
                ),
                field="disposition_date",
                context=disposition_context,
            ),
            "matched_qty": _quantize_qty(
                _coerce_decimal(
                    value=_read_required_field(
                        record=disposition,
                        field="matched_qty",
                        context=disposition_context,
                    ),
                    field="matched_qty",
                    context=disposition_context,
                )
            ),
            "matched_cost_basis_usd": _quantize_money(
                _coerce_decimal(
                    value=_read_required_field(
                        record=disposition,
                        field="matched_cost_basis_usd",
                        context=disposition_context,
                    ),
                    field="matched_cost_basis_usd",
                    context=disposition_context,
                )
            ),
            "sell_gross_amount_usd": sell_gross_amount_usd,
        }
        cast(list[dict[str, object]], lot_payload["dispositions"]).append(disposition_payload)

    for lot_payload in selected_lots:
        lot_disposition_payloads = cast(list[dict[str, object]], lot_payload["dispositions"])
        lot_disposition_payloads.sort(
            key=lambda item: (
                cast(date, item["disposition_date"]).isoformat(),
                cast(int, item["sell_transaction_id"]),
            )
        )

    selected_lots.sort(
        key=lambda item: (
            cast(date, item["opened_on"]).isoformat(),
            cast(int, item["lot_id"]),
        )
    )
    return {
        "instrument_symbol": normalized_symbol,
        "lots": selected_lots,
    }


async def _fetch_as_of_ledger_at(*, db: AsyncSession) -> datetime:
    """Return one ledger-state timestamp used for analytics response consistency."""

    timestamp_candidates: list[datetime] = []
    max_queries = (
        select(func.max(PortfolioTransaction.updated_at)),
        select(func.max(DividendEvent.updated_at)),
        select(func.max(Lot.updated_at)),
        select(func.max(LotDisposition.updated_at)),
    )
    for query in max_queries:
        result = await db.execute(query)
        candidate = result.scalar_one_or_none()
        if isinstance(candidate, datetime):
            timestamp_candidates.append(candidate)

    if not timestamp_candidates:
        return utcnow()
    return max(timestamp_candidates)


async def _set_repeatable_read_snapshot(*, db: AsyncSession) -> None:
    """Set one consistent read-only snapshot for analytics reads."""

    await db.execute(
        text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"),
    )


def _serialize_lot_row(lot: Lot) -> dict[str, object]:
    """Serialize one lot ORM row for analytics builders."""

    return {
        "id": lot.id,
        "instrument_symbol": lot.instrument_symbol,
        "opened_on": lot.opened_on,
        "original_qty": lot.original_qty,
        "remaining_qty": lot.remaining_qty,
        "total_cost_basis_usd": lot.total_cost_basis_usd,
        "unit_cost_basis_usd": lot.unit_cost_basis_usd,
    }


def _serialize_lot_disposition_row(lot_disposition: LotDisposition) -> dict[str, object]:
    """Serialize one lot-disposition ORM row for analytics builders."""

    return {
        "lot_id": lot_disposition.lot_id,
        "sell_transaction_id": lot_disposition.sell_transaction_id,
        "disposition_date": lot_disposition.disposition_date,
        "matched_qty": lot_disposition.matched_qty,
        "matched_cost_basis_usd": lot_disposition.matched_cost_basis_usd,
    }


def _serialize_portfolio_transaction_row(
    portfolio_transaction: PortfolioTransaction,
) -> dict[str, object]:
    """Serialize one trade-ledger ORM row for analytics builders."""

    return {
        "id": portfolio_transaction.id,
        "instrument_symbol": portfolio_transaction.instrument_symbol,
        "event_date": portfolio_transaction.event_date,
        "trade_side": portfolio_transaction.trade_side,
        "gross_amount_usd": portfolio_transaction.gross_amount_usd,
    }


def _serialize_dividend_event_row(dividend_event: DividendEvent) -> dict[str, object]:
    """Serialize one dividend-event ORM row for analytics builders."""

    return {
        "instrument_symbol": dividend_event.instrument_symbol,
        "gross_amount_usd": dividend_event.gross_amount_usd,
        "taxes_withheld_usd": dividend_event.taxes_withheld_usd,
        "net_amount_usd": dividend_event.net_amount_usd,
    }


def _read_required_field(
    *,
    record: Mapping[str, object],
    field: str,
    context: str,
) -> object:
    """Read one required field from a mapping with fail-fast validation."""

    if field not in record:
        raise PortfolioAnalyticsClientError(
            f"Required field '{field}' is missing in {context} input.",
            status_code=422,
        )
    value = record[field]
    if value is None:
        raise PortfolioAnalyticsClientError(
            f"Required field '{field}' is null in {context} input.",
            status_code=422,
        )
    return value


def _coerce_decimal(*, value: object, field: str, context: str) -> Decimal:
    """Coerce one numeric input value to finite decimal."""

    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, int):
        decimal_value = Decimal(value)
    elif isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            raise PortfolioAnalyticsClientError(
                f"Field '{field}' in {context} input must not be empty.",
                status_code=422,
            )
        try:
            decimal_value = Decimal(stripped_value)
        except InvalidOperation as exc:
            raise PortfolioAnalyticsClientError(
                f"Field '{field}' in {context} input must be a valid decimal.",
                status_code=422,
            ) from exc
    else:
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' in {context} input must be numeric.",
            status_code=422,
        )

    if not decimal_value.is_finite():
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' in {context} input must be a finite decimal.",
            status_code=422,
        )
    return decimal_value


def _coerce_positive_int(*, value: object, field: str, context: str) -> int:
    """Coerce one required integer field and require positive value."""

    if isinstance(value, bool):
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' in {context} input must be an integer.",
            status_code=422,
        )
    if isinstance(value, int):
        integer_value = value
    elif isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            raise PortfolioAnalyticsClientError(
                f"Field '{field}' in {context} input must not be empty.",
                status_code=422,
            )
        if not stripped_value.isdigit():
            raise PortfolioAnalyticsClientError(
                f"Field '{field}' in {context} input must be an integer.",
                status_code=422,
            )
        integer_value = int(stripped_value)
    else:
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' in {context} input must be an integer.",
            status_code=422,
        )

    if integer_value <= 0:
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' in {context} input must be greater than zero.",
            status_code=422,
        )
    return integer_value


def _coerce_date(*, value: object, field: str, context: str) -> date:
    """Coerce one required date field from string or date object."""

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value:
            raise PortfolioAnalyticsClientError(
                f"Field '{field}' in {context} input must not be empty.",
                status_code=422,
            )
        try:
            return date.fromisoformat(stripped_value)
        except ValueError as exc:
            raise PortfolioAnalyticsClientError(
                f"Field '{field}' in {context} input must use YYYY-MM-DD format.",
                status_code=422,
            ) from exc
    raise PortfolioAnalyticsClientError(
        f"Field '{field}' in {context} input must be a date.",
        status_code=422,
    )


def _normalize_symbol(*, symbol_value: object, field: str) -> str:
    """Normalize one instrument symbol deterministically."""

    if not isinstance(symbol_value, str):
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' must be a string instrument symbol.",
            status_code=422,
        )
    normalized_symbol = symbol_value.strip().upper()
    if not normalized_symbol:
        raise PortfolioAnalyticsClientError(
            f"Field '{field}' must not be empty.",
            status_code=422,
        )
    return normalized_symbol


def _quantize_qty(value: Decimal) -> Decimal:
    """Quantize quantity-like decimals to fixed scale."""

    return value.quantize(_QTY_SCALE)


def _quantize_money(value: Decimal) -> Decimal:
    """Quantize currency-like decimals to fixed scale."""

    return value.quantize(_MONEY_SCALE)
