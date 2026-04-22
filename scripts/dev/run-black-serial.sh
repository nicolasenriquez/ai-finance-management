#!/usr/bin/env bash
set -euo pipefail

uv run python - "$@" <<'PY'
from __future__ import annotations

import difflib
import sys
from pathlib import Path

import black
from black.report import NothingChanged


def parse_args(argv: list[str]) -> tuple[bool, bool, list[str]]:
    """Parse wrapper flags and collect file paths."""

    check = False
    show_diff = False
    files: list[str] = []
    index = 0

    while index < len(argv):
      arg = argv[index]
      if arg == "--check":
          check = True
      elif arg == "--diff":
          show_diff = True
      elif arg == "--":
          files.extend(argv[index + 1 :])
          break
      else:
          files.append(arg)
      index += 1

    if not files:
        for line in sys.stdin:
            file = line.strip()
            if file:
                files.append(file)

    return check, show_diff, files


def write_diff(path: Path, original: str, formatted: str) -> None:
    """Emit a unified diff for a single file."""

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        formatted.splitlines(keepends=True),
        fromfile=str(path),
        tofile=str(path),
    )
    sys.stdout.writelines(diff)


def main() -> int:
    """Run Black in-process over each file to avoid multiprocessing."""

    check, show_diff, files = parse_args(sys.argv[1:])
    if not files:
        return 0

    exit_code = 0
    mode_kwargs: dict[str, object] = {}
    pyproject = black.find_pyproject_toml((str(Path.cwd()),))
    if pyproject:
        parsed_config = black.parse_pyproject_toml(pyproject)
        line_length = parsed_config.get("line_length")
        if isinstance(line_length, int):
            mode_kwargs["line_length"] = line_length

    mode = black.FileMode(**mode_kwargs)

    for raw_path in files:
        path = Path(raw_path)
        original = path.read_text()
        try:
            formatted = black.format_file_contents(original, fast=False, mode=mode)
        except NothingChanged:
            formatted = original

        if formatted == original:
            continue

        if check:
            exit_code = 1
            if show_diff:
                write_diff(path, original, formatted)
            continue

        path.write_text(formatted)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
PY
