#!/bin/sh
set -eu

: "${POSTGRES_USER:?POSTGRES_USER must be set}"
: "${POSTGRES_APP_USER:?POSTGRES_APP_USER must be set}"
: "${POSTGRES_APP_PASSWORD:?POSTGRES_APP_PASSWORD must be set}"
: "${POSTGRES_APP_DB:?POSTGRES_APP_DB must be set}"

psql \
  -v ON_ERROR_STOP=1 \
  -v app_user="$POSTGRES_APP_USER" \
  -v app_password="$POSTGRES_APP_PASSWORD" \
  -v app_db="$POSTGRES_APP_DB" \
  --username "$POSTGRES_USER" \
  --dbname postgres <<'EOSQL'
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_catalog.pg_roles
        WHERE rolname = :'app_user'
    ) THEN
        EXECUTE format(
            'CREATE ROLE %I LOGIN PASSWORD %L',
            :'app_user',
            :'app_password'
        );
    END IF;
END
$$;

SELECT format(
    'CREATE DATABASE %I OWNER %I',
    :'app_db',
    :'app_user'
)
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = :'app_db'
)\gexec
EOSQL

psql \
  -v ON_ERROR_STOP=1 \
  -v app_user="$POSTGRES_APP_USER" \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_APP_DB" <<'EOSQL'
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO :"app_user";
EOSQL
