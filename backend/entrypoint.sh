#!/bin/sh
set -e

# Apply database migrations before starting the API so the schema is ready.
alembic upgrade head

# Hot-reload only in local development (APP_ENV=development); production runs without it.
RELOAD=""
[ "$APP_ENV" = "development" ] && RELOAD="--reload"

exec uvicorn main:app --host 0.0.0.0 --port 8000 --log-config log_config.json $RELOAD
