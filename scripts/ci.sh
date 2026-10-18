#!/usr/bin/env bash
# Run every backend check against disposable dependencies. Extra arguments go to pytest.
# Removes only the containers and volumes it created, even when a check fails.
set -euo pipefail

cd "$(dirname "$0")/../backend"

project="dietsheet-ci-$$"
compose=(docker compose --progress quiet -p "$project" -f tests/compose.yaml)
cleanup() { "${compose[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "==> sync locked dependencies"
uv sync --frozen

echo "==> lint and format"
uv run ruff check .
uv run ruff format --check .

echo "==> type check"
uv run mypy

echo "==> architecture rules"
uv run lint-imports

echo "==> start disposable Postgres"
"${compose[@]}" up --detach --wait db >/dev/null
port="$("${compose[@]}" port db 5432 | cut -d: -f2)"

echo "==> tests"
DATABASE_URL="postgresql+psycopg://dietsheet:dietsheet-test-only@127.0.0.1:${port}/dietsheet" \
    uv run pytest "$@"
