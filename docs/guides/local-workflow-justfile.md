# Local Workflow with Justfile

## Purpose

This guide defines the recommended local developer workflow using repository `just` recipes.

Use it to:

- bootstrap dependencies
- run the local app stack
- run backend/frontend validation gates before push or PR

## Install Just

macOS (Homebrew):

```bash
brew install just
```

Verify:

```bash
just --version
```

## Bootstrap

```bash
cp .env.example .env
just install
```

If PostgreSQL is not already running from Postgres.app, start Docker DB:

```bash
docker-compose up -d db
```

## Run App Locally

Run backend + frontend together:

```bash
just dev
```

Endpoints:

- backend: `http://localhost:8123`
- frontend: `http://localhost:3000`

Run components individually:

```bash
just backend
just frontend
```

## Validation Gates

Backend-focused gates:

```bash
just lint
just type
just security
just test
just test-integration
just backend-ci
```

Frontend-focused gates:

```bash
just frontend-lint
just frontend-type
just frontend-test
just frontend-build
just frontend-ci
```

Full local pre-CI gate:

```bash
just ci
```

## Git Hooks

Install hooks:

```bash
just precommit-install
```

Run hooks manually:

```bash
just precommit-run
```
