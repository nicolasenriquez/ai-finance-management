"""Service helpers for portfolio-ledger event derivation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import cast

from pydantic import ValidationError
from sqlalchemy import delete, or_, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.session import SessionTransactionOrigin

from app.core.logging import get_logger
from app.pdf_persistence.models import CanonicalPdfRecord
from app.portfolio_ledger.accounting import (
    DATASET_1_V1_ACCOUNTING_POLICY,
    apply_split_to_open_lots,
    match_sell_trade_fifo,
)
from app.portfolio_ledger.models import (
    CorporateActionEvent,
    DividendEvent,
    Lot,
    LotDisposition,
    PortfolioTransaction,
)
from app.portfolio_ledger.schemas import (
    LedgerEventSeed,
    LedgerEventType,
    LedgerLineage,
    LedgerTargetTable,
    PersistedCanonicalRecord,
)
from app.shared.models import utcnow

logger = get_logger(__name__)

_QTY_SCALE = Decimal("0.000000001")
_MONEY_SCALE = Decimal("0.01")
_UNIT_COST_BASIS_SCALE = Decimal("0.000000001")


@dataclass
class _LotState:
    """In-memory deterministic lot state during one rebuild run."""

    opening_transaction_id: int
    instrument_symbol: str
    opened_on: date
    original_qty: Decimal
    remaining_qty: Decimal
    total_cost_basis_usd: Decimal
    unit_cost_basis_usd: Decimal
    last_corporate_action_event_id: int | None = None


@dataclass
class _DispositionState:
    """In-memory lot-disposition state during one rebuild run."""

    opening_transaction_id: int
    sell_transaction_id: int
    disposition_date: date
    matched_qty: Decimal
    matched_cost_basis_usd: Decimal


class PortfolioLedgerClientError(ValueError):
    """Raised when portfolio-ledger derivation input is invalid or unsafe."""

    status_code: int

    def __init__(self, message: str, *, status_code: int) -> None:
        """Initialize client-facing ledger derivation error."""

        super().__init__(message)
        self.status_code = status_code


def map_canonical_record_to_ledger_event(*, record: Mapping[str, object]) -> dict[str, object]:
    """Map one persisted canonical record to a typed ledger event seed."""

    persisted_record = _parse_persisted_canonical_record(record=record)
    event_seed = _build_ledger_event_seed(record=persisted_record)

    return {
        "target_table": event_seed.target_table.value,
        "event_type": event_seed.event_type.value,
        "event_date": event_seed.event_date,
        "instrument_symbol": event_seed.instrument_symbol,
        "lineage": event_seed.lineage.model_dump(mode="python"),
        "canonical_payload": dict(event_seed.canonical_payload),
    }


async def rebuild_portfolio_ledger_from_canonical_records(
    *,
    source_document_id: int,
    db: AsyncSession,
) -> dict[str, object]:
    """Derive ledger events from persisted canonical rows transactionally."""

    normalized_source_document_id = _coerce_positive_int(
        source_document_id,
        field="source_document_id",
    )
    logger.info(
        "portfolio_ledger.rebuild_started",
        source_document_id=normalized_source_document_id,
    )

    try:
        if _get_transaction_origin(db=db) is SessionTransactionOrigin.AUTOBEGIN:
            async with AsyncSession(
                bind=db.bind,
                expire_on_commit=False,
                autoflush=False,
            ) as isolated_db:
                async with isolated_db.begin():
                    await _clear_lot_state_for_source_document(
                        source_document_id=normalized_source_document_id,
                        db=isolated_db,
                    )
                    event_counts = await _derive_and_persist_ledger_events(
                        source_document_id=normalized_source_document_id,
                        db=isolated_db,
                    )
                    await _clear_lot_state_for_source_document(
                        source_document_id=normalized_source_document_id,
                        db=isolated_db,
                    )
                    lot_counts = await _derive_and_persist_lot_state(
                        source_document_id=normalized_source_document_id,
                        db=isolated_db,
                    )
        elif db.in_transaction():
            async with db.begin_nested():
                await _clear_lot_state_for_source_document(
                    source_document_id=normalized_source_document_id,
                    db=db,
                )
                event_counts = await _derive_and_persist_ledger_events(
                    source_document_id=normalized_source_document_id,
                    db=db,
                )
                await _clear_lot_state_for_source_document(
                    source_document_id=normalized_source_document_id,
                    db=db,
                )
                lot_counts = await _derive_and_persist_lot_state(
                    source_document_id=normalized_source_document_id,
                    db=db,
                )
        else:
            async with db.begin():
                await _clear_lot_state_for_source_document(
                    source_document_id=normalized_source_document_id,
                    db=db,
                )
                event_counts = await _derive_and_persist_ledger_events(
                    source_document_id=normalized_source_document_id,
                    db=db,
                )
                await _clear_lot_state_for_source_document(
                    source_document_id=normalized_source_document_id,
                    db=db,
                )
                lot_counts = await _derive_and_persist_lot_state(
                    source_document_id=normalized_source_document_id,
                    db=db,
                )
    except PortfolioLedgerClientError as exc:
        logger.info(
            "portfolio_ledger.rebuild_rejected",
            source_document_id=normalized_source_document_id,
            status_code=exc.status_code,
            error=str(exc),
        )
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "portfolio_ledger.rebuild_failed",
            source_document_id=normalized_source_document_id,
            error=str(exc),
            error_type=type(exc).__name__,
            exc_info=True,
        )
        raise PortfolioLedgerClientError(
            "Failed to rebuild portfolio ledger due to a database error.",
            status_code=500,
        ) from exc

    counts = {**event_counts, **lot_counts}

    logger.info(
        "portfolio_ledger.rebuild_completed",
        source_document_id=normalized_source_document_id,
        processed_records=counts["processed_records"],
        portfolio_transactions=counts["portfolio_transactions"],
        dividend_events=counts["dividend_events"],
        corporate_action_events=counts["corporate_action_events"],
        open_lots=counts["open_lots"],
        lot_dispositions=counts["lot_dispositions"],
    )
    return {
        "source_document_id": normalized_source_document_id,
        "processed_records": counts["processed_records"],
        "portfolio_transactions": counts["portfolio_transactions"],
        "dividend_events": counts["dividend_events"],
        "corporate_action_events": counts["corporate_action_events"],
        "open_lots": counts["open_lots"],
        "lot_dispositions": counts["lot_dispositions"],
    }


def _get_transaction_origin(
    *,
    db: AsyncSession,
) -> SessionTransactionOrigin | None:
    """Return the current SQLAlchemy transaction origin when available."""

    current_transaction = db.get_transaction()
    if current_transaction is None:
        return None

    sync_transaction = current_transaction.sync_transaction
    if sync_transaction is None:
        return None

    return sync_transaction.origin


async def _derive_and_persist_ledger_events(
    *,
    source_document_id: int,
    db: AsyncSession,
) -> dict[str, int]:
    """Derive and insert ledger-domain events for one source document."""

    records_result = await db.execute(
        select(CanonicalPdfRecord)
        .where(CanonicalPdfRecord.source_document_id == source_document_id)
        .order_by(CanonicalPdfRecord.event_date.asc(), CanonicalPdfRecord.id.asc()),
    )
    canonical_records = records_result.scalars().all()

    processed_records = 0
    portfolio_transactions = 0
    dividend_events = 0
    corporate_action_events = 0
    trade_canonical_record_ids: set[int] = set()
    dividend_canonical_record_ids: set[int] = set()
    corporate_action_canonical_record_ids: set[int] = set()

    for canonical_record in canonical_records:
        persisted_record = _persisted_canonical_record_from_model(
            canonical_record=canonical_record,
        )
        event_seed = _build_ledger_event_seed(record=persisted_record)
        await _insert_derived_event(
            event_seed=event_seed,
            persisted_record=persisted_record,
            db=db,
        )
        processed_records += 1

        if event_seed.target_table is LedgerTargetTable.PORTFOLIO_TRANSACTION:
            portfolio_transactions += 1
            trade_canonical_record_ids.add(persisted_record.canonical_record_id)
        elif event_seed.target_table is LedgerTargetTable.DIVIDEND_EVENT:
            dividend_events += 1
            dividend_canonical_record_ids.add(persisted_record.canonical_record_id)
        else:
            corporate_action_events += 1
            corporate_action_canonical_record_ids.add(persisted_record.canonical_record_id)

    await _prune_stale_ledger_event_rows(
        source_document_id=source_document_id,
        trade_canonical_record_ids=trade_canonical_record_ids,
        dividend_canonical_record_ids=dividend_canonical_record_ids,
        corporate_action_canonical_record_ids=corporate_action_canonical_record_ids,
        db=db,
    )

    return {
        "processed_records": processed_records,
        "portfolio_transactions": portfolio_transactions,
        "dividend_events": dividend_events,
        "corporate_action_events": corporate_action_events,
    }


async def _derive_and_persist_lot_state(
    *,
    source_document_id: int,
    db: AsyncSession,
) -> dict[str, int]:
    """Derive and persist deterministic lot and lot-disposition state."""

    transactions_result = await db.execute(
        select(PortfolioTransaction)
        .where(PortfolioTransaction.source_document_id == source_document_id)
        .order_by(PortfolioTransaction.event_date.asc(), PortfolioTransaction.id.asc()),
    )
    transactions = list(transactions_result.scalars().all())

    corporate_actions_result = await db.execute(
        select(CorporateActionEvent)
        .where(CorporateActionEvent.source_document_id == source_document_id)
        .order_by(CorporateActionEvent.event_date.asc(), CorporateActionEvent.id.asc()),
    )
    corporate_actions = list(corporate_actions_result.scalars().all())

    lot_states: dict[int, _LotState] = {}
    disposition_states: dict[tuple[int, int], _DispositionState] = {}

    event_stream: list[tuple[date, int, int, str]] = []
    for transaction in transactions:
        event_stream.append(
            (
                transaction.event_date,
                transaction.canonical_record_id,
                transaction.id,
                "trade",
            )
        )
    for corporate_action in corporate_actions:
        event_stream.append(
            (
                corporate_action.event_date,
                corporate_action.canonical_record_id,
                corporate_action.id,
                "split",
            )
        )
    event_stream.sort()

    transaction_by_id = {transaction.id: transaction for transaction in transactions}
    corporate_action_by_id = {
        corporate_action.id: corporate_action for corporate_action in corporate_actions
    }

    for _, _, event_id, event_kind in event_stream:
        if event_kind == "trade":
            trade_event = transaction_by_id.get(event_id)
            if trade_event is None:
                raise PortfolioLedgerClientError(
                    "Portfolio transaction event stream contains unknown trade id.",
                    status_code=500,
                )
            _apply_trade_event_to_lot_state(
                transaction=trade_event,
                lot_states=lot_states,
                disposition_states=disposition_states,
            )
            continue

        split_event = corporate_action_by_id.get(event_id)
        if split_event is None:
            raise PortfolioLedgerClientError(
                "Corporate-action event stream contains unknown split id.",
                status_code=500,
            )
        _apply_split_event_to_lot_state(
            corporate_action_event=split_event,
            lot_states=lot_states,
        )

    lot_id_by_opening_transaction_id = await _upsert_lot_rows(
        lot_states=lot_states,
        db=db,
    )
    disposition_count = await _upsert_lot_disposition_rows(
        disposition_states=disposition_states,
        lot_id_by_opening_transaction_id=lot_id_by_opening_transaction_id,
        db=db,
    )

    open_lot_count = sum(
        1 for lot_state in lot_states.values() if lot_state.remaining_qty > Decimal("0")
    )
    return {
        "open_lots": open_lot_count,
        "lot_dispositions": disposition_count,
    }


def _apply_trade_event_to_lot_state(
    *,
    transaction: PortfolioTransaction,
    lot_states: dict[int, _LotState],
    disposition_states: dict[tuple[int, int], _DispositionState],
) -> None:
    """Apply one trade event to in-memory lot and lot-disposition state."""

    if transaction.trade_side == "buy":
        lot_states[transaction.id] = _initial_lot_state_from_buy_transaction(
            transaction=transaction
        )
        return

    if transaction.trade_side == "sell":
        _apply_sell_transaction_to_lot_state(
            transaction=transaction,
            lot_states=lot_states,
            disposition_states=disposition_states,
        )
        return

    raise PortfolioLedgerClientError(
        f"Unsupported portfolio transaction trade_side: {transaction.trade_side!r}.",
        status_code=422,
    )


def _initial_lot_state_from_buy_transaction(*, transaction: PortfolioTransaction) -> _LotState:
    """Build initial lot state from one buy-side portfolio transaction."""

    quantity = _coerce_positive_decimal_for_lot(
        transaction.quantity,
        field="quantity",
    ).quantize(_QTY_SCALE, rounding=ROUND_HALF_UP)
    total_cost_basis_usd = _coerce_non_negative_decimal_for_lot(
        transaction.gross_amount_usd,
        field="gross_amount_usd",
    ).quantize(_MONEY_SCALE, rounding=ROUND_HALF_UP)

    unit_cost_basis_usd = (total_cost_basis_usd / quantity).quantize(
        _UNIT_COST_BASIS_SCALE,
        rounding=ROUND_HALF_UP,
    )
    return _LotState(
        opening_transaction_id=transaction.id,
        instrument_symbol=transaction.instrument_symbol,
        opened_on=transaction.event_date,
        original_qty=quantity,
        remaining_qty=quantity,
        total_cost_basis_usd=total_cost_basis_usd,
        unit_cost_basis_usd=unit_cost_basis_usd,
        last_corporate_action_event_id=None,
    )


def _apply_sell_transaction_to_lot_state(
    *,
    transaction: PortfolioTransaction,
    lot_states: dict[int, _LotState],
    disposition_states: dict[tuple[int, int], _DispositionState],
) -> None:
    """Apply one sell trade against open lots using FIFO matching."""

    open_lot_candidates = sorted(
        (
            lot_state
            for lot_state in lot_states.values()
            if lot_state.instrument_symbol == transaction.instrument_symbol
            and lot_state.remaining_qty > Decimal("0")
        ),
        key=lambda lot_state: (lot_state.opened_on, lot_state.opening_transaction_id),
    )

    if not open_lot_candidates:
        raise PortfolioLedgerClientError(
            (
                "Sell transaction cannot be matched because no open lots exist for "
                f"instrument {transaction.instrument_symbol!r}."
            ),
            status_code=422,
        )

    open_lot_payload = [
        _lot_state_payload(lot_state=lot_state) for lot_state in open_lot_candidates
    ]
    sell_trade_payload = {
        "sold_qty": _format_decimal(
            value=_coerce_positive_decimal_for_lot(
                transaction.quantity,
                field="quantity",
            ),
            scale=_QTY_SCALE,
        ),
        "proceeds_usd": _format_decimal(
            value=_coerce_non_negative_decimal_for_lot(
                transaction.gross_amount_usd,
                field="gross_amount_usd",
            ),
            scale=_MONEY_SCALE,
        ),
    }

    try:
        match_result = match_sell_trade_fifo(
            open_lots=open_lot_payload,
            sell_trade=sell_trade_payload,
        )
    except ValueError as exc:
        raise PortfolioLedgerClientError(
            f"FIFO sell matching failed: {exc}",
            status_code=422,
        ) from exc

    dispositions = _coerce_dispositions_sequence(match_result.get("dispositions"))

    for disposition in dispositions:
        opening_transaction_id = _coerce_positive_int(
            disposition.get("lot_id"),
            field="lot_id",
        )
        matched_qty = _coerce_non_negative_decimal_for_lot(
            disposition.get("matched_qty"),
            field="matched_qty",
        ).quantize(_QTY_SCALE, rounding=ROUND_HALF_UP)
        matched_cost_basis_usd = _coerce_non_negative_decimal_for_lot(
            disposition.get("matched_cost_basis_usd"),
            field="matched_cost_basis_usd",
        ).quantize(_MONEY_SCALE, rounding=ROUND_HALF_UP)

        lot_state = lot_states.get(opening_transaction_id)
        if lot_state is None:
            raise PortfolioLedgerClientError(
                (
                    "FIFO disposition references unknown opening_transaction_id "
                    f"{opening_transaction_id}."
                ),
                status_code=500,
            )

        updated_remaining_qty = (lot_state.remaining_qty - matched_qty).quantize(
            _QTY_SCALE,
            rounding=ROUND_HALF_UP,
        )
        if updated_remaining_qty < Decimal("0"):
            raise PortfolioLedgerClientError(
                (
                    "FIFO disposition produced negative remaining quantity for "
                    f"opening_transaction_id={opening_transaction_id}."
                ),
                status_code=500,
            )
        prior_total_cost_basis_usd = lot_state.total_cost_basis_usd
        matched_cost_basis_to_apply = matched_cost_basis_usd
        if updated_remaining_qty == Decimal("0"):
            matched_cost_basis_to_apply = prior_total_cost_basis_usd

        updated_total_cost_basis_usd = (
            prior_total_cost_basis_usd - matched_cost_basis_to_apply
        ).quantize(
            _MONEY_SCALE,
            rounding=ROUND_HALF_UP,
        )
        if updated_total_cost_basis_usd < Decimal("0"):
            raise PortfolioLedgerClientError(
                (
                    "FIFO disposition produced negative remaining cost basis for "
                    f"opening_transaction_id={opening_transaction_id}."
                ),
                status_code=500,
            )

        lot_state.remaining_qty = updated_remaining_qty
        lot_state.total_cost_basis_usd = updated_total_cost_basis_usd

        disposition_states[(opening_transaction_id, transaction.id)] = _DispositionState(
            opening_transaction_id=opening_transaction_id,
            sell_transaction_id=transaction.id,
            disposition_date=transaction.event_date,
            matched_qty=matched_qty,
            matched_cost_basis_usd=matched_cost_basis_to_apply,
        )


def _apply_split_event_to_lot_state(
    *,
    corporate_action_event: CorporateActionEvent,
    lot_states: dict[int, _LotState],
) -> None:
    """Apply one split event to open lot state for the affected instrument."""

    open_lot_candidates = sorted(
        (
            lot_state
            for lot_state in lot_states.values()
            if lot_state.instrument_symbol == corporate_action_event.instrument_symbol
            and lot_state.remaining_qty > Decimal("0")
        ),
        key=lambda lot_state: (lot_state.opened_on, lot_state.opening_transaction_id),
    )
    if not open_lot_candidates:
        return

    split_payload = {
        "split_ratio_value": _format_decimal(
            value=_coerce_positive_decimal_for_lot(
                corporate_action_event.split_ratio_value,
                field="split_ratio_value",
            ),
            scale=_QTY_SCALE,
        ),
    }

    open_lot_payload = [
        _lot_state_payload(lot_state=lot_state) for lot_state in open_lot_candidates
    ]
    try:
        adjusted_lots = apply_split_to_open_lots(
            open_lots=open_lot_payload,
            split_event=split_payload,
        )
    except ValueError as exc:
        raise PortfolioLedgerClientError(
            f"Split lot adjustment failed: {exc}",
            status_code=422,
        ) from exc

    adjusted_lot_rows = _coerce_dispositions_sequence(adjusted_lots)
    for adjusted_lot in adjusted_lot_rows:
        opening_transaction_id = _coerce_positive_int(
            adjusted_lot.get("lot_id"),
            field="lot_id",
        )
        lot_state = lot_states.get(opening_transaction_id)
        if lot_state is None:
            raise PortfolioLedgerClientError(
                (
                    "Split adjustment references unknown opening_transaction_id "
                    f"{opening_transaction_id}."
                ),
                status_code=500,
            )

        lot_state.remaining_qty = _coerce_non_negative_decimal_for_lot(
            adjusted_lot.get("remaining_qty"),
            field="remaining_qty",
        ).quantize(
            _QTY_SCALE,
            rounding=ROUND_HALF_UP,
        )
        lot_state.total_cost_basis_usd = _coerce_non_negative_decimal_for_lot(
            adjusted_lot.get("total_cost_basis_usd"),
            field="total_cost_basis_usd",
        ).quantize(
            _MONEY_SCALE,
            rounding=ROUND_HALF_UP,
        )
        lot_state.unit_cost_basis_usd = _coerce_non_negative_decimal_for_lot(
            adjusted_lot.get("unit_cost_basis_usd"),
            field="unit_cost_basis_usd",
        ).quantize(
            _UNIT_COST_BASIS_SCALE,
            rounding=ROUND_HALF_UP,
        )
        lot_state.last_corporate_action_event_id = corporate_action_event.id


async def _upsert_lot_rows(
    *,
    lot_states: Mapping[int, _LotState],
    db: AsyncSession,
) -> dict[int, int]:
    """Persist deterministic lot state rows with conflict-safe upsert semantics."""

    for lot_state in lot_states.values():
        statement = (
            postgresql_insert(Lot)
            .values(
                opening_transaction_id=lot_state.opening_transaction_id,
                last_corporate_action_event_id=lot_state.last_corporate_action_event_id,
                instrument_symbol=lot_state.instrument_symbol,
                opened_on=lot_state.opened_on,
                original_qty=lot_state.original_qty,
                remaining_qty=lot_state.remaining_qty,
                total_cost_basis_usd=lot_state.total_cost_basis_usd,
                unit_cost_basis_usd=lot_state.unit_cost_basis_usd,
                accounting_policy_version=DATASET_1_V1_ACCOUNTING_POLICY.version.value,
            )
            .on_conflict_do_update(
                constraint="uq_lot_opening_tx",
                set_={
                    "last_corporate_action_event_id": lot_state.last_corporate_action_event_id,
                    "instrument_symbol": lot_state.instrument_symbol,
                    "opened_on": lot_state.opened_on,
                    "original_qty": lot_state.original_qty,
                    "remaining_qty": lot_state.remaining_qty,
                    "total_cost_basis_usd": lot_state.total_cost_basis_usd,
                    "unit_cost_basis_usd": lot_state.unit_cost_basis_usd,
                    "accounting_policy_version": DATASET_1_V1_ACCOUNTING_POLICY.version.value,
                    "updated_at": utcnow(),
                },
            )
        )
        await db.execute(statement)

    if not lot_states:
        return {}

    opening_transaction_ids = tuple(lot_states.keys())
    lot_rows_result = await db.execute(
        select(Lot).where(Lot.opening_transaction_id.in_(opening_transaction_ids)),
    )
    lot_rows = lot_rows_result.scalars().all()
    lot_id_by_opening_transaction_id = {
        lot_row.opening_transaction_id: lot_row.id for lot_row in lot_rows
    }
    if len(lot_id_by_opening_transaction_id) != len(lot_states):
        raise PortfolioLedgerClientError(
            "Failed to resolve lot rows by opening_transaction_id during rebuild.",
            status_code=500,
        )
    return lot_id_by_opening_transaction_id


async def _clear_lot_state_for_source_document(
    *,
    source_document_id: int,
    db: AsyncSession,
) -> None:
    """Delete lot and lot-disposition rows for one source document."""

    transaction_ids_subquery = select(PortfolioTransaction.id).where(
        PortfolioTransaction.source_document_id == source_document_id,
    )
    lot_ids_subquery = select(Lot.id).where(
        Lot.opening_transaction_id.in_(transaction_ids_subquery),
    )
    await db.execute(
        delete(LotDisposition).where(
            or_(
                LotDisposition.lot_id.in_(lot_ids_subquery),
                LotDisposition.sell_transaction_id.in_(transaction_ids_subquery),
            )
        ),
    )
    await db.execute(
        delete(Lot).where(Lot.opening_transaction_id.in_(transaction_ids_subquery)),
    )


async def _prune_stale_ledger_event_rows(
    *,
    source_document_id: int,
    trade_canonical_record_ids: set[int],
    dividend_canonical_record_ids: set[int],
    corporate_action_canonical_record_ids: set[int],
    db: AsyncSession,
) -> None:
    """Delete stale derived event rows by event type for one source document."""

    if corporate_action_canonical_record_ids:
        corporate_action_ids = tuple(corporate_action_canonical_record_ids)
        await db.execute(
            delete(CorporateActionEvent).where(
                CorporateActionEvent.source_document_id == source_document_id,
                CorporateActionEvent.canonical_record_id.notin_(corporate_action_ids),
            ),
        )
    else:
        await db.execute(
            delete(CorporateActionEvent).where(
                CorporateActionEvent.source_document_id == source_document_id,
            ),
        )

    if dividend_canonical_record_ids:
        dividend_ids = tuple(dividend_canonical_record_ids)
        await db.execute(
            delete(DividendEvent).where(
                DividendEvent.source_document_id == source_document_id,
                DividendEvent.canonical_record_id.notin_(dividend_ids),
            ),
        )
    else:
        await db.execute(
            delete(DividendEvent).where(
                DividendEvent.source_document_id == source_document_id,
            ),
        )

    if trade_canonical_record_ids:
        trade_ids = tuple(trade_canonical_record_ids)
        await db.execute(
            delete(PortfolioTransaction).where(
                PortfolioTransaction.source_document_id == source_document_id,
                PortfolioTransaction.canonical_record_id.notin_(trade_ids),
            ),
        )
    else:
        await db.execute(
            delete(PortfolioTransaction).where(
                PortfolioTransaction.source_document_id == source_document_id,
            ),
        )


async def _upsert_lot_disposition_rows(
    *,
    disposition_states: Mapping[tuple[int, int], _DispositionState],
    lot_id_by_opening_transaction_id: Mapping[int, int],
    db: AsyncSession,
) -> int:
    """Persist deterministic lot-disposition rows with conflict-safe upsert semantics."""

    for disposition_state in disposition_states.values():
        lot_id = lot_id_by_opening_transaction_id.get(disposition_state.opening_transaction_id)
        if lot_id is None:
            raise PortfolioLedgerClientError(
                (
                    "Lot disposition references unknown opening_transaction_id "
                    f"{disposition_state.opening_transaction_id}."
                ),
                status_code=500,
            )

        statement = (
            postgresql_insert(LotDisposition)
            .values(
                lot_id=lot_id,
                sell_transaction_id=disposition_state.sell_transaction_id,
                disposition_date=disposition_state.disposition_date,
                matched_qty=disposition_state.matched_qty,
                matched_cost_basis_usd=disposition_state.matched_cost_basis_usd,
                accounting_policy_version=DATASET_1_V1_ACCOUNTING_POLICY.version.value,
            )
            .on_conflict_do_update(
                constraint="uq_lot_disposition_lot_sell_tx",
                set_={
                    "disposition_date": disposition_state.disposition_date,
                    "matched_qty": disposition_state.matched_qty,
                    "matched_cost_basis_usd": disposition_state.matched_cost_basis_usd,
                    "accounting_policy_version": DATASET_1_V1_ACCOUNTING_POLICY.version.value,
                    "updated_at": utcnow(),
                },
            )
        )
        await db.execute(statement)

    return len(disposition_states)


def _lot_state_payload(*, lot_state: _LotState) -> dict[str, str]:
    """Return deterministic lot payload used by accounting helpers."""

    return {
        "lot_id": str(lot_state.opening_transaction_id),
        "remaining_qty": _format_decimal(
            value=lot_state.remaining_qty,
            scale=_QTY_SCALE,
        ),
        "total_cost_basis_usd": _format_decimal(
            value=lot_state.total_cost_basis_usd,
            scale=_MONEY_SCALE,
        ),
        "unit_cost_basis_usd": _format_decimal(
            value=lot_state.unit_cost_basis_usd,
            scale=_UNIT_COST_BASIS_SCALE,
        ),
    }


def _persisted_canonical_record_from_model(
    *,
    canonical_record: CanonicalPdfRecord,
) -> PersistedCanonicalRecord:
    """Convert persisted canonical row model to typed ledger service input."""

    try:
        return PersistedCanonicalRecord(
            canonical_record_id=canonical_record.id,
            source_document_id=canonical_record.source_document_id,
            import_job_id=canonical_record.import_job_id,
            fingerprint=canonical_record.fingerprint,
            event_type=_coerce_event_type(canonical_record.event_type),
            event_date=canonical_record.event_date,
            instrument_symbol=canonical_record.instrument_symbol,
            trade_side=canonical_record.trade_side,
            canonical_payload=dict(canonical_record.canonical_payload),
        )
    except ValidationError as exc:
        raise PortfolioLedgerClientError(
            "Persisted canonical record cannot be converted to typed ledger input.",
            status_code=500,
        ) from exc


def _parse_persisted_canonical_record(
    *,
    record: Mapping[str, object],
) -> PersistedCanonicalRecord:
    """Validate persisted canonical mapping payload as typed service input."""

    record_id = record.get("canonical_record_id")
    if record_id is None:
        record_id = record.get("id")

    canonical_payload = _coerce_payload_mapping(
        record.get("canonical_payload"),
        field="canonical_payload",
    )
    trade_side_value = record.get("trade_side")
    trade_side: str | None = (
        None
        if trade_side_value is None
        else _coerce_non_empty_str(trade_side_value, field="trade_side")
    )

    try:
        return PersistedCanonicalRecord(
            canonical_record_id=_coerce_positive_int(
                record_id,
                field="canonical_record_id",
            ),
            source_document_id=_coerce_positive_int(
                record.get("source_document_id"),
                field="source_document_id",
            ),
            import_job_id=_coerce_positive_int(
                record.get("import_job_id"),
                field="import_job_id",
            ),
            fingerprint=_coerce_non_empty_str(
                record.get("fingerprint"),
                field="fingerprint",
            ),
            event_type=_coerce_event_type(record.get("event_type")),
            event_date=_coerce_date(
                record.get("event_date"),
                field="event_date",
            ),
            instrument_symbol=_coerce_non_empty_str(
                record.get("instrument_symbol"),
                field="instrument_symbol",
            ),
            trade_side=trade_side,
            canonical_payload=canonical_payload,
        )
    except ValidationError as exc:
        raise PortfolioLedgerClientError(
            "Persisted canonical record is invalid for ledger mapping.",
            status_code=422,
        ) from exc


def _build_ledger_event_seed(*, record: PersistedCanonicalRecord) -> LedgerEventSeed:
    """Build typed event-seed payload from persisted canonical input."""

    target_table = _target_table_for_event(event_type=record.event_type)

    return LedgerEventSeed(
        target_table=target_table,
        event_type=record.event_type,
        event_date=record.event_date,
        instrument_symbol=record.instrument_symbol,
        lineage=LedgerLineage(
            source_document_id=record.source_document_id,
            import_job_id=record.import_job_id,
            canonical_record_id=record.canonical_record_id,
            canonical_fingerprint=record.fingerprint,
        ),
        canonical_payload=dict(record.canonical_payload),
    )


def _target_table_for_event(*, event_type: LedgerEventType) -> LedgerTargetTable:
    """Map canonical event type to ledger target table."""

    if event_type is LedgerEventType.TRADE:
        return LedgerTargetTable.PORTFOLIO_TRANSACTION
    if event_type is LedgerEventType.DIVIDEND:
        return LedgerTargetTable.DIVIDEND_EVENT
    if event_type is LedgerEventType.SPLIT:
        return LedgerTargetTable.CORPORATE_ACTION_EVENT
    raise PortfolioLedgerClientError(
        f"Unsupported canonical event type for ledger mapping: {event_type!s}",
        status_code=422,
    )


async def _insert_derived_event(
    *,
    event_seed: LedgerEventSeed,
    persisted_record: PersistedCanonicalRecord,
    db: AsyncSession,
) -> None:
    """Insert or update one derived ledger event row for deterministic rebuild."""

    if event_seed.target_table is LedgerTargetTable.PORTFOLIO_TRANSACTION:
        trade_row = _build_portfolio_transaction_row(
            event_seed=event_seed,
            persisted_record=persisted_record,
        )
        statement = (
            postgresql_insert(PortfolioTransaction)
            .values(
                source_document_id=trade_row.source_document_id,
                import_job_id=trade_row.import_job_id,
                canonical_record_id=trade_row.canonical_record_id,
                canonical_fingerprint=trade_row.canonical_fingerprint,
                event_date=trade_row.event_date,
                instrument_symbol=trade_row.instrument_symbol,
                trade_side=trade_row.trade_side,
                quantity=trade_row.quantity,
                gross_amount_usd=trade_row.gross_amount_usd,
                accounting_policy_version=trade_row.accounting_policy_version,
                canonical_payload=trade_row.canonical_payload,
            )
            .on_conflict_do_update(
                constraint="uq_portfolio_transaction_canonical_record_id",
                set_={
                    "source_document_id": trade_row.source_document_id,
                    "import_job_id": trade_row.import_job_id,
                    "canonical_fingerprint": trade_row.canonical_fingerprint,
                    "event_date": trade_row.event_date,
                    "instrument_symbol": trade_row.instrument_symbol,
                    "trade_side": trade_row.trade_side,
                    "quantity": trade_row.quantity,
                    "gross_amount_usd": trade_row.gross_amount_usd,
                    "accounting_policy_version": trade_row.accounting_policy_version,
                    "canonical_payload": trade_row.canonical_payload,
                    "updated_at": utcnow(),
                },
            )
        )
        await db.execute(statement)
    elif event_seed.target_table is LedgerTargetTable.DIVIDEND_EVENT:
        dividend_row = _build_dividend_event_row(
            event_seed=event_seed,
            persisted_record=persisted_record,
        )
        statement = (
            postgresql_insert(DividendEvent)
            .values(
                source_document_id=dividend_row.source_document_id,
                import_job_id=dividend_row.import_job_id,
                canonical_record_id=dividend_row.canonical_record_id,
                canonical_fingerprint=dividend_row.canonical_fingerprint,
                event_date=dividend_row.event_date,
                instrument_symbol=dividend_row.instrument_symbol,
                gross_amount_usd=dividend_row.gross_amount_usd,
                taxes_withheld_usd=dividend_row.taxes_withheld_usd,
                net_amount_usd=dividend_row.net_amount_usd,
                accounting_policy_version=dividend_row.accounting_policy_version,
                canonical_payload=dividend_row.canonical_payload,
            )
            .on_conflict_do_update(
                constraint="uq_dividend_event_canonical_record_id",
                set_={
                    "source_document_id": dividend_row.source_document_id,
                    "import_job_id": dividend_row.import_job_id,
                    "canonical_fingerprint": dividend_row.canonical_fingerprint,
                    "event_date": dividend_row.event_date,
                    "instrument_symbol": dividend_row.instrument_symbol,
                    "gross_amount_usd": dividend_row.gross_amount_usd,
                    "taxes_withheld_usd": dividend_row.taxes_withheld_usd,
                    "net_amount_usd": dividend_row.net_amount_usd,
                    "accounting_policy_version": dividend_row.accounting_policy_version,
                    "canonical_payload": dividend_row.canonical_payload,
                    "updated_at": utcnow(),
                },
            )
        )
        await db.execute(statement)
    elif event_seed.target_table is LedgerTargetTable.CORPORATE_ACTION_EVENT:
        split_row = _build_corporate_action_event_row(
            event_seed=event_seed,
            persisted_record=persisted_record,
        )
        statement = (
            postgresql_insert(CorporateActionEvent)
            .values(
                source_document_id=split_row.source_document_id,
                import_job_id=split_row.import_job_id,
                canonical_record_id=split_row.canonical_record_id,
                canonical_fingerprint=split_row.canonical_fingerprint,
                event_date=split_row.event_date,
                instrument_symbol=split_row.instrument_symbol,
                action_type=split_row.action_type,
                shares_before_qty=split_row.shares_before_qty,
                shares_after_qty=split_row.shares_after_qty,
                split_ratio_value=split_row.split_ratio_value,
                accounting_policy_version=split_row.accounting_policy_version,
                canonical_payload=split_row.canonical_payload,
            )
            .on_conflict_do_update(
                constraint="uq_corporate_action_event_canonical_record_id",
                set_={
                    "source_document_id": split_row.source_document_id,
                    "import_job_id": split_row.import_job_id,
                    "canonical_fingerprint": split_row.canonical_fingerprint,
                    "event_date": split_row.event_date,
                    "instrument_symbol": split_row.instrument_symbol,
                    "action_type": split_row.action_type,
                    "shares_before_qty": split_row.shares_before_qty,
                    "shares_after_qty": split_row.shares_after_qty,
                    "split_ratio_value": split_row.split_ratio_value,
                    "accounting_policy_version": split_row.accounting_policy_version,
                    "canonical_payload": split_row.canonical_payload,
                    "updated_at": utcnow(),
                },
            )
        )
        await db.execute(statement)
    else:
        raise PortfolioLedgerClientError(
            f"Unsupported target table for ledger insert: {event_seed.target_table!s}",
            status_code=422,
        )


def _build_portfolio_transaction_row(
    *,
    event_seed: LedgerEventSeed,
    persisted_record: PersistedCanonicalRecord,
) -> PortfolioTransaction:
    """Build one portfolio-transaction row from trade canonical payload."""

    trade_side = _normalize_trade_side(
        trade_side=persisted_record.trade_side,
        canonical_record_id=persisted_record.canonical_record_id,
    )
    quantity_field, amount_field = _trade_payload_fields_for_side(trade_side=trade_side)

    quantity = _get_required_decimal(
        payload=persisted_record.canonical_payload,
        field=quantity_field,
        canonical_record_id=persisted_record.canonical_record_id,
    )
    gross_amount_usd = _get_required_decimal(
        payload=persisted_record.canonical_payload,
        field=amount_field,
        canonical_record_id=persisted_record.canonical_record_id,
    )

    return PortfolioTransaction(
        source_document_id=event_seed.lineage.source_document_id,
        import_job_id=event_seed.lineage.import_job_id,
        canonical_record_id=event_seed.lineage.canonical_record_id,
        canonical_fingerprint=event_seed.lineage.canonical_fingerprint,
        event_date=event_seed.event_date,
        instrument_symbol=event_seed.instrument_symbol,
        trade_side=trade_side,
        quantity=quantity,
        gross_amount_usd=gross_amount_usd,
        accounting_policy_version=DATASET_1_V1_ACCOUNTING_POLICY.version.value,
        canonical_payload=dict(event_seed.canonical_payload),
    )


def _build_dividend_event_row(
    *,
    event_seed: LedgerEventSeed,
    persisted_record: PersistedCanonicalRecord,
) -> DividendEvent:
    """Build one dividend-event row from dividend canonical payload."""

    gross_amount_usd = _get_required_decimal(
        payload=persisted_record.canonical_payload,
        field="gross_usd",
        canonical_record_id=persisted_record.canonical_record_id,
    )
    taxes_withheld_usd = _get_required_decimal(
        payload=persisted_record.canonical_payload,
        field="taxes_usd",
        canonical_record_id=persisted_record.canonical_record_id,
    )
    net_amount_usd = _get_required_decimal(
        payload=persisted_record.canonical_payload,
        field="net_usd",
        canonical_record_id=persisted_record.canonical_record_id,
    )

    return DividendEvent(
        source_document_id=event_seed.lineage.source_document_id,
        import_job_id=event_seed.lineage.import_job_id,
        canonical_record_id=event_seed.lineage.canonical_record_id,
        canonical_fingerprint=event_seed.lineage.canonical_fingerprint,
        event_date=event_seed.event_date,
        instrument_symbol=event_seed.instrument_symbol,
        gross_amount_usd=gross_amount_usd,
        taxes_withheld_usd=taxes_withheld_usd,
        net_amount_usd=net_amount_usd,
        accounting_policy_version=DATASET_1_V1_ACCOUNTING_POLICY.version.value,
        canonical_payload=dict(event_seed.canonical_payload),
    )


def _build_corporate_action_event_row(
    *,
    event_seed: LedgerEventSeed,
    persisted_record: PersistedCanonicalRecord,
) -> CorporateActionEvent:
    """Build one corporate-action event row from split canonical payload."""

    shares_before_qty = _get_required_decimal(
        payload=persisted_record.canonical_payload,
        field="shares_before_qty",
        canonical_record_id=persisted_record.canonical_record_id,
    )
    shares_after_qty = _get_required_decimal(
        payload=persisted_record.canonical_payload,
        field="shares_after_qty",
        canonical_record_id=persisted_record.canonical_record_id,
    )
    split_ratio_value = _get_required_decimal(
        payload=persisted_record.canonical_payload,
        field="split_ratio_value",
        canonical_record_id=persisted_record.canonical_record_id,
    )

    return CorporateActionEvent(
        source_document_id=event_seed.lineage.source_document_id,
        import_job_id=event_seed.lineage.import_job_id,
        canonical_record_id=event_seed.lineage.canonical_record_id,
        canonical_fingerprint=event_seed.lineage.canonical_fingerprint,
        event_date=event_seed.event_date,
        instrument_symbol=event_seed.instrument_symbol,
        action_type=LedgerEventType.SPLIT.value,
        shares_before_qty=shares_before_qty,
        shares_after_qty=shares_after_qty,
        split_ratio_value=split_ratio_value,
        accounting_policy_version=DATASET_1_V1_ACCOUNTING_POLICY.version.value,
        canonical_payload=dict(event_seed.canonical_payload),
    )


def _trade_payload_fields_for_side(*, trade_side: str) -> tuple[str, str]:
    """Return payload quantity and amount fields for one trade-side direction."""

    if trade_side == "buy":
        return (
            "acciones_compradas_qty",
            DATASET_1_V1_ACCOUNTING_POLICY.buy_cost_basis_field,
        )
    if trade_side == "sell":
        return (
            "acciones_vendidas_qty",
            DATASET_1_V1_ACCOUNTING_POLICY.sell_proceeds_field,
        )
    raise PortfolioLedgerClientError(
        f"Unsupported trade_side for ledger derivation: {trade_side}",
        status_code=422,
    )


def _normalize_trade_side(*, trade_side: str | None, canonical_record_id: int) -> str:
    """Normalize and validate trade-side string from canonical input."""

    if trade_side is None:
        raise PortfolioLedgerClientError(
            "Trade canonical record is missing required trade_side.",
            status_code=422,
        )

    normalized_trade_side = trade_side.strip().lower()
    if normalized_trade_side not in {"buy", "sell"}:
        raise PortfolioLedgerClientError(
            (
                "Trade canonical record has unsupported trade_side "
                f"{trade_side!r} (canonical_record_id={canonical_record_id})."
            ),
            status_code=422,
        )
    return normalized_trade_side


def _get_required_decimal(
    *,
    payload: Mapping[str, object],
    field: str,
    canonical_record_id: int,
) -> Decimal:
    """Extract one required decimal payload value or raise explicit client error."""

    raw_value = payload.get(field)
    if raw_value is None:
        raise PortfolioLedgerClientError(
            (
                f"Canonical payload field '{field}' is required for ledger derivation "
                f"(canonical_record_id={canonical_record_id})."
            ),
            status_code=422,
        )
    return _coerce_decimal(
        value=raw_value,
        field=field,
        canonical_record_id=canonical_record_id,
    )


def _coerce_dispositions_sequence(value: object) -> list[Mapping[str, object]]:
    """Coerce a sequence payload into list[Mapping[str, object]]."""

    if not isinstance(value, list):
        raise PortfolioLedgerClientError(
            "Expected list payload for accounting dispositions.",
            status_code=500,
        )

    raw_rows = cast(list[object], value)
    rows: list[Mapping[str, object]] = []
    for raw_row in raw_rows:
        if not isinstance(raw_row, Mapping):
            raise PortfolioLedgerClientError(
                "Accounting disposition row must be a mapping.",
                status_code=500,
            )
        rows.append(cast(Mapping[str, object], raw_row))
    return rows


def _coerce_non_negative_decimal_for_lot(value: object, *, field: str) -> Decimal:
    """Coerce one decimal value and enforce non-negative lot semantics."""

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise PortfolioLedgerClientError(
            f"{field} must be a valid decimal value for lot derivation.",
            status_code=422,
        ) from exc

    if decimal_value < Decimal("0"):
        raise PortfolioLedgerClientError(
            f"{field} must be non-negative for lot derivation.",
            status_code=422,
        )
    return decimal_value


def _coerce_positive_decimal_for_lot(value: object, *, field: str) -> Decimal:
    """Coerce one decimal value and enforce positive lot semantics."""

    decimal_value = _coerce_non_negative_decimal_for_lot(value, field=field)
    if decimal_value <= Decimal("0"):
        raise PortfolioLedgerClientError(
            f"{field} must be greater than zero for lot derivation.",
            status_code=422,
        )
    return decimal_value


def _format_decimal(*, value: Decimal, scale: Decimal) -> str:
    """Format a decimal value with deterministic fixed-point precision."""

    return format(value.quantize(scale, rounding=ROUND_HALF_UP), "f")


def _coerce_decimal(*, value: object, field: str, canonical_record_id: int) -> Decimal:
    """Coerce one scalar value to decimal with explicit fail-fast validation."""

    if isinstance(value, bool):
        raise PortfolioLedgerClientError(
            (
                f"Canonical payload field '{field}' must be numeric, got bool "
                f"(canonical_record_id={canonical_record_id})."
            ),
            status_code=422,
        )

    decimal_value: Decimal
    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, int):
        decimal_value = Decimal(value)
    elif isinstance(value, float):
        decimal_value = Decimal(str(value))
    elif isinstance(value, str):
        normalized_value = value.strip()
        if not normalized_value:
            raise PortfolioLedgerClientError(
                (
                    f"Canonical payload field '{field}' is empty "
                    f"(canonical_record_id={canonical_record_id})."
                ),
                status_code=422,
            )
        try:
            decimal_value = Decimal(normalized_value)
        except InvalidOperation as exc:
            raise PortfolioLedgerClientError(
                (
                    f"Canonical payload field '{field}' is not a valid decimal "
                    f"(canonical_record_id={canonical_record_id})."
                ),
                status_code=422,
            ) from exc
    else:
        raise PortfolioLedgerClientError(
            (
                f"Canonical payload field '{field}' has unsupported type "
                f"{type(value).__name__} (canonical_record_id={canonical_record_id})."
            ),
            status_code=422,
        )

    if not decimal_value.is_finite():
        raise PortfolioLedgerClientError(
            (
                f"Canonical payload field '{field}' must be a finite decimal "
                f"(canonical_record_id={canonical_record_id})."
            ),
            status_code=422,
        )
    return decimal_value


def _coerce_positive_int(value: object, *, field: str) -> int:
    """Coerce one integer-like value and enforce positive semantics."""

    if isinstance(value, bool):
        raise PortfolioLedgerClientError(
            f"{field} must be a positive integer.",
            status_code=422,
        )

    if isinstance(value, int):
        if value >= 1:
            return value
        raise PortfolioLedgerClientError(
            f"{field} must be a positive integer.",
            status_code=422,
        )

    if isinstance(value, str):
        normalized_value = value.strip()
        if normalized_value.isdigit():
            int_value = int(normalized_value)
            if int_value >= 1:
                return int_value

    raise PortfolioLedgerClientError(
        f"{field} must be a positive integer.",
        status_code=422,
    )


def _coerce_non_empty_str(value: object, *, field: str) -> str:
    """Coerce one value to non-empty string."""

    if not isinstance(value, str):
        raise PortfolioLedgerClientError(
            f"{field} must be a non-empty string.",
            status_code=422,
        )

    normalized_value = value.strip()
    if not normalized_value:
        raise PortfolioLedgerClientError(
            f"{field} must be a non-empty string.",
            status_code=422,
        )
    return normalized_value


def _coerce_event_type(value: object) -> LedgerEventType:
    """Coerce one raw event type value into typed ledger event enum."""

    if isinstance(value, LedgerEventType):
        return value
    if not isinstance(value, str):
        raise PortfolioLedgerClientError(
            "event_type must be a supported canonical event string.",
            status_code=422,
        )
    try:
        return LedgerEventType(value.strip())
    except ValueError as exc:
        raise PortfolioLedgerClientError(
            f"Unsupported canonical event_type: {value!r}.",
            status_code=422,
        ) from exc


def _coerce_date(value: object, *, field: str) -> date:
    """Coerce one date-like value into a date object."""

    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        normalized_value = value.strip()
        if not normalized_value:
            raise PortfolioLedgerClientError(
                f"{field} must be a valid date value.",
                status_code=422,
            )
        try:
            return date.fromisoformat(normalized_value)
        except ValueError as exc:
            raise PortfolioLedgerClientError(
                f"{field} must be a valid ISO date string.",
                status_code=422,
            ) from exc
    raise PortfolioLedgerClientError(
        f"{field} must be a valid date value.",
        status_code=422,
    )


def _coerce_payload_mapping(value: object, *, field: str) -> dict[str, object]:
    """Coerce one mapping-like payload to a dictionary with string keys."""

    if not isinstance(value, Mapping):
        raise PortfolioLedgerClientError(
            f"{field} must be a mapping for ledger derivation.",
            status_code=422,
        )

    mapping_value = cast(Mapping[object, object], value)
    payload: dict[str, object] = {}
    for raw_key, raw_value in mapping_value.items():
        if not isinstance(raw_key, str):
            raise PortfolioLedgerClientError(
                f"{field} keys must be strings for ledger derivation.",
                status_code=422,
            )
        payload[raw_key] = raw_value
    return payload
