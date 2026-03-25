"""CLI entrypoints for local dataset bootstrap and yfinance market refresh operations."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from app.data_sync.service import (
    DataSyncClientError,
    run_data_sync_local,
    run_dataset1_bootstrap,
    run_market_refresh_yfinance,
)


def parse_iso_datetime(value: str) -> datetime:
    """Parse one timezone-aware ISO datetime argument for snapshot capture time."""

    normalized_value = value.strip()
    if normalized_value.endswith("Z"):
        normalized_value = f"{normalized_value[:-1]}+00:00"

    try:
        parsed_value = datetime.fromisoformat(normalized_value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "snapshot-captured-at must be an ISO datetime string."
        ) from exc

    if parsed_value.tzinfo is None or parsed_value.tzinfo.utcoffset(parsed_value) is None:
        raise argparse.ArgumentTypeError(
            "snapshot-captured-at must include timezone information (for example +00:00 or Z)."
        )
    return parsed_value


def build_parser() -> argparse.ArgumentParser:
    """Build command parser for local data-sync operation entrypoints."""

    parser = argparse.ArgumentParser(
        description=(
            "Run local data-sync operations: dataset bootstrap, yfinance refresh, "
            "or combined sync."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = subparsers.add_parser(
        "data-bootstrap-dataset1",
        help="Run dataset_1 bootstrap (ingest -> persist -> rebuild).",
    )
    bootstrap_parser.add_argument(
        "--dataset-pdf-path",
        type=Path,
        default=None,
        help="Optional override for dataset PDF path.",
    )

    refresh_parser = subparsers.add_parser(
        "market-refresh-yfinance",
        help="Run yfinance supported-universe market refresh.",
    )
    refresh_parser.add_argument(
        "--snapshot-captured-at",
        type=parse_iso_datetime,
        default=None,
        help="Optional timezone-aware snapshot capture datetime.",
    )

    sync_parser = subparsers.add_parser(
        "data-sync-local",
        help="Run dataset bootstrap then yfinance market refresh (fail-fast).",
    )
    sync_parser.add_argument(
        "--dataset-pdf-path",
        type=Path,
        default=None,
        help="Optional override for dataset PDF path.",
    )
    sync_parser.add_argument(
        "--snapshot-captured-at",
        type=parse_iso_datetime,
        default=None,
        help="Optional timezone-aware snapshot capture datetime.",
    )

    return parser


def _print_result(payload: BaseModel) -> None:
    """Print one result model as deterministic JSON."""

    print(
        json.dumps(
            payload.model_dump(mode="json"),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
    )


def _print_failure(*, error: str, stage: str, status_code: int) -> None:
    """Print one fail-fast command error payload to stderr."""

    print(
        json.dumps(
            {
                "status": "failed",
                "stage": stage,
                "status_code": status_code,
                "error": error,
            },
            ensure_ascii=True,
            sort_keys=True,
        ),
        file=sys.stderr,
    )


async def async_main() -> int:
    """Run the selected local data-sync command and return process exit code."""

    parser = build_parser()
    args = parser.parse_args()
    from app.core.database import AsyncSessionLocal

    try:
        async with AsyncSessionLocal() as db:
            if args.command == "data-bootstrap-dataset1":
                bootstrap_result = await run_dataset1_bootstrap(
                    db=db,
                    dataset_pdf_path=args.dataset_pdf_path,
                )
                _print_result(bootstrap_result)
                return 0

            if args.command == "market-refresh-yfinance":
                refresh_result = await run_market_refresh_yfinance(
                    db=db,
                    snapshot_captured_at=args.snapshot_captured_at,
                )
                _print_result(refresh_result)
                return 0

            if args.command == "data-sync-local":
                sync_result = await run_data_sync_local(
                    db=db,
                    dataset_pdf_path=args.dataset_pdf_path,
                    snapshot_captured_at=args.snapshot_captured_at,
                )
                _print_result(sync_result)
                return 0

            _print_failure(
                error=f"Unsupported command: {args.command}",
                stage="input",
                status_code=422,
            )
            return 1
    except DataSyncClientError as exc:
        _print_failure(
            error=str(exc),
            stage=exc.stage,
            status_code=exc.status_code,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
