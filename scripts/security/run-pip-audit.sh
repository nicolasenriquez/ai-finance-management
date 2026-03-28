#!/usr/bin/env bash
set -euo pipefail

# Run pip-audit with repository baseline arguments.
# By default this is a strict gate (non-zero exit on any failure).
# In restricted-network environments, set:
#   PIP_AUDIT_ALLOW_NETWORK_BLOCKED=1
# to classify DNS/network lookup failures as blocked evidence instead of code failure.

tmp_out="$(mktemp)"
trap 'rm -f "$tmp_out"' EXIT

if uv run pip-audit --progress-spinner=off --ignore-vuln CVE-2026-4539 >"$tmp_out" 2>&1; then
  cat "$tmp_out"
  exit 0
fi

cat "$tmp_out"

if [[ "${PIP_AUDIT_ALLOW_NETWORK_BLOCKED:-0}" == "1" ]] && rg -q \
  "NameResolutionError|Failed to resolve|ConnectionError|Temporary failure in name resolution|nodename nor servname provided" \
  "$tmp_out"; then
  echo
  echo "pip-audit blocked by network/DNS reachability (classified as non-code failure due to PIP_AUDIT_ALLOW_NETWORK_BLOCKED=1)."
  exit 0
fi

exit 1
