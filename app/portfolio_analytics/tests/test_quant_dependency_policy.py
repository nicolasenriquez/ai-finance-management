"""Dependency policy tests for approved runtime quant stack usage."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import cast

import pytest

_APPROVED_QUANT_PACKAGES: tuple[str, ...] = ("numpy", "pandas", "scipy")
_REJECTED_QUANT_PACKAGES: tuple[str, ...] = (
    "zipline",
    "zipline-reloaded",
    "pyfolio",
    "pyrisk",
    "mibian",
    "backtrader",
    "quantlib-python",
)


def _repo_root() -> Path:
    """Return repository root path from this test module location."""

    return Path(__file__).resolve().parents[3]


def _normalize_package_name(name: str) -> str:
    """Normalize package name to PEP 503 comparable form."""

    return name.strip().lower().replace("_", "-").replace(".", "-")


def _extract_requirement_name(requirement: str) -> str:
    """Extract package name from one dependency requirement string."""

    marker_split = requirement.split(";", maxsplit=1)[0]
    requirement_prefix = marker_split.split("[", maxsplit=1)[0]
    match = re.match(r"^\s*([A-Za-z0-9_.-]+)", requirement_prefix)
    if match is None:
        pytest.fail(f"Unable to parse dependency requirement: {requirement!r}")
    return _normalize_package_name(match.group(1))


def _load_pyproject_runtime_dependencies() -> list[str]:
    """Load runtime dependency strings from pyproject.toml."""

    pyproject_path = _repo_root() / "pyproject.toml"
    pyproject_data = _coerce_dict(
        tomllib.loads(pyproject_path.read_text(encoding="utf-8")),
        context="pyproject.toml root",
    )
    project_section = _coerce_dict(
        pyproject_data.get("project"),
        context="pyproject.toml [project]",
    )

    dependencies = project_section.get("dependencies")
    if not isinstance(dependencies, list):
        pytest.fail("pyproject.toml [project].dependencies must be a list.")
    dependency_entries = cast(list[object], dependencies)

    normalized_dependencies: list[str] = []
    for dependency in dependency_entries:
        if not isinstance(dependency, str):
            pytest.fail("pyproject.toml dependencies must be requirement strings.")
        normalized_dependencies.append(dependency)
    return normalized_dependencies


def _load_uv_lock() -> dict[str, object]:
    """Load uv.lock as TOML data."""

    uv_lock_path = _repo_root() / "uv.lock"
    return _coerce_dict(
        tomllib.loads(uv_lock_path.read_text(encoding="utf-8")),
        context="uv.lock root",
    )


def _coerce_dict(value: object, *, context: str) -> dict[str, object]:
    """Coerce object into dict[str, object] with explicit test failure on mismatch."""

    if not isinstance(value, dict):
        pytest.fail(f"{context} must be an object.")
    dict_value = cast(dict[object, object], value)
    if not all(isinstance(key, str) for key in dict_value):
        pytest.fail(f"{context} must have string keys.")
    return cast(dict[str, object], dict_value)


def _coerce_dict_list(value: object, *, context: str) -> list[dict[str, object]]:
    """Coerce object into list[dict[str, object]] with explicit test failure on mismatch."""

    if not isinstance(value, list):
        pytest.fail(f"{context} must be a list.")
    list_value = cast(list[object], value)

    resolved_entries: list[dict[str, object]] = []
    for index, entry in enumerate(list_value):
        resolved_entries.append(_coerce_dict(entry, context=f"{context}[{index}]"))
    return resolved_entries


def _build_runtime_dependency_closure(
    package_entries: Iterable[dict[str, object]],
    runtime_roots: set[str],
) -> set[str]:
    """Build runtime dependency closure using package dependency metadata."""

    dependency_graph: dict[str, set[str]] = {}
    for package_entry in package_entries:
        raw_name = package_entry.get("name")
        if not isinstance(raw_name, str):
            pytest.fail("uv.lock package entry missing string 'name'.")

        package_name = _normalize_package_name(raw_name)
        dependencies = _coerce_dict_list(
            package_entry.get("dependencies", []),
            context=f"uv.lock dependencies for {package_name}",
        )

        resolved_dependencies: set[str] = set()
        for dependency in dependencies:
            dependency_name = dependency.get("name")
            if not isinstance(dependency_name, str):
                pytest.fail(
                    f"uv.lock dependency entry for {package_name} is missing string 'name'.",
                )
            resolved_dependencies.add(_normalize_package_name(dependency_name))

        dependency_graph[package_name] = resolved_dependencies

    visited: set[str] = set()
    stack: list[str] = sorted(runtime_roots)
    while stack:
        package_name = stack.pop()
        if package_name in visited:
            continue
        visited.add(package_name)
        stack.extend(sorted(dependency_graph.get(package_name, set()) - visited))

    return visited


def test_runtime_quant_dependencies_are_exact_pins_and_lock_synced() -> None:
    """Approved runtime quant packages must be exact pins and lock-synced."""

    runtime_dependencies = _load_pyproject_runtime_dependencies()
    runtime_dependency_by_name = {
        _extract_requirement_name(requirement): requirement for requirement in runtime_dependencies
    }

    uv_lock_data = _load_uv_lock()
    package_entries = _coerce_dict_list(
        uv_lock_data.get("package"),
        context="uv.lock package entries",
    )

    package_versions: dict[str, str] = {}
    root_package_requires_dist: dict[str, str] = {}
    for package_entry in package_entries:
        raw_name = package_entry.get("name")
        raw_version = package_entry.get("version")
        if isinstance(raw_name, str) and isinstance(raw_version, str):
            package_versions[_normalize_package_name(raw_name)] = raw_version

        if raw_name == "ai-finance-management":
            metadata = _coerce_dict(
                package_entry.get("metadata"),
                context="uv.lock root metadata",
            )

            requires_dist = _coerce_dict_list(
                metadata.get("requires-dist"),
                context="uv.lock root metadata requires-dist",
            )

            for requirement in requires_dist:
                requirement_name = requirement.get("name")
                requirement_specifier = requirement.get("specifier", "")
                if not isinstance(requirement_name, str) or not isinstance(
                    requirement_specifier, str
                ):
                    pytest.fail("uv.lock requires-dist entry must include string name/specifier.")
                root_package_requires_dist[_normalize_package_name(requirement_name)] = (
                    requirement_specifier
                )

    for package_name in _APPROVED_QUANT_PACKAGES:
        runtime_entry = runtime_dependency_by_name.get(package_name)
        if runtime_entry is None:
            pytest.fail(f"Runtime dependency '{package_name}' must be declared in pyproject.toml.")

        exact_pin_match = re.fullmatch(
            rf"{re.escape(package_name)}==([A-Za-z0-9.+-]+)", runtime_entry
        )
        if exact_pin_match is None:
            pytest.fail(
                f"Runtime dependency '{runtime_entry}' must use an exact pin '==<version>'.",
            )

        pinned_version = exact_pin_match.group(1)
        requires_dist_specifier = root_package_requires_dist.get(package_name)
        if requires_dist_specifier != f"=={pinned_version}":
            pytest.fail(
                "uv.lock root requires-dist must mirror the exact quant pin for "
                f"{package_name}: expected '=={pinned_version}', got {requires_dist_specifier!r}.",
            )

        lock_version = package_versions.get(package_name)
        if lock_version != pinned_version:
            pytest.fail(
                f"uv.lock package version mismatch for {package_name}: "
                f"expected {pinned_version}, got {lock_version!r}.",
            )


def test_rejected_quant_packages_are_absent_from_runtime_dependency_closure() -> None:
    """Rejected quant packages must not appear in runtime dependency closure."""

    uv_lock_data = _load_uv_lock()
    package_entries = _coerce_dict_list(
        uv_lock_data.get("package"),
        context="uv.lock package entries",
    )

    runtime_roots: set[str] = set()
    for package_entry in package_entries:
        if package_entry.get("name") != "ai-finance-management":
            continue

        dependencies = _coerce_dict_list(
            package_entry.get("dependencies"),
            context="uv.lock root package dependencies",
        )

        for dependency in dependencies:
            dependency_name = dependency.get("name")
            if not isinstance(dependency_name, str):
                pytest.fail("uv.lock root dependency entry missing string 'name'.")
            runtime_roots.add(_normalize_package_name(dependency_name))
        break

    if not runtime_roots:
        pytest.fail("uv.lock root runtime dependencies could not be resolved.")

    runtime_closure = _build_runtime_dependency_closure(package_entries, runtime_roots)
    rejected_intersection = runtime_closure.intersection(_REJECTED_QUANT_PACKAGES)
    assert not rejected_intersection, (
        "Rejected quant packages must not be present in runtime dependency closure: "
        f"{sorted(rejected_intersection)}"
    )
