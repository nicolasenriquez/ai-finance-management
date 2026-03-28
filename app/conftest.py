"""Global pytest safety guards for repository test execution."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def require_integration_mutation_flag(request: pytest.FixtureRequest) -> None:
    """Fail fast unless integration tests are explicitly authorized.

    This guard prevents accidental execution of integration tests that truncate or
    mutate database state when developers run `pytest` directly against a non-test
    runtime environment.
    """

    if "integration" not in request.keywords:
        return

    if os.getenv("ALLOW_INTEGRATION_DB_MUTATION") == "1":
        return

    raise RuntimeError(
        "Integration tests require explicit authorization. "
        "Set ALLOW_INTEGRATION_DB_MUTATION=1 (or use just test-integration)."
    )
