#!/bin/sh
set -e

# Apply database migrations before starting the API so `docker compose up`
# brings up a ready-to-use schema.
alembic upgrade head

exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
