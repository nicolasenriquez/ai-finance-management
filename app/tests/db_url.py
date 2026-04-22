"""Helpers to resolve an isolated test database URL for pytest fixtures."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.engine import make_url


def resolve_test_database_url(*, runtime_database_url: str) -> str:
    """Resolve the database URL that pytest fixtures must use.

    Resolution order:
    1. Explicit ``TEST_DATABASE_URL`` from process environment.
    2. ``TEST_DATABASE_URL`` from local ``.env`` file.
    3. Runtime ``DATABASE_URL`` only when it already points to a ``*_test`` database.

    Args:
        runtime_database_url: Effective ``DATABASE_URL`` loaded by application settings.

    Returns:
        The isolated test database URL.

    Raises:
        RuntimeError: If no safe isolated test database URL can be resolved.
    """

    explicit_test_url = _read_env_var("TEST_DATABASE_URL") or _read_env_file_value(
        key="TEST_DATABASE_URL"
    )
    runtime_db_name = _database_name_from_url(runtime_database_url)

    if explicit_test_url:
        explicit_test_db_name = _database_name_from_url(explicit_test_url)
        if not explicit_test_db_name.endswith("_test"):
            raise RuntimeError("TEST_DATABASE_URL must point to a database ending with '_test'.")
        return explicit_test_url

    if runtime_db_name.endswith("_test"):
        return runtime_database_url

    raise RuntimeError(
        "Unsafe pytest DB configuration: runtime DATABASE_URL does not point to a "
        "test database and TEST_DATABASE_URL is missing. "
        "Set TEST_DATABASE_URL (recommended) or run tests with DATABASE_URL targeting "
        "a '*_test' database."
    )


def _read_env_var(key: str) -> str:
    """Read one environment variable as a stripped string."""

    import os

    return os.getenv(key, "").strip()


def _read_env_file_value(*, key: str) -> str:
    """Read one key value from local .env file, if present."""

    env_path = Path(".env")
    if not env_path.is_file():
        return ""

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        candidate_key, raw_value = line.split("=", 1)
        if candidate_key.strip() != key:
            continue

        value = raw_value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        return value.strip()

    return ""


def _database_name_from_url(database_url: str) -> str:
    """Extract database name from one SQLAlchemy URL."""

    parsed_url = make_url(database_url)
    if not parsed_url.database:
        raise RuntimeError("Database URL must include a database name.")
    return parsed_url.database
