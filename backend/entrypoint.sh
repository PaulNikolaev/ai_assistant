#!/bin/sh
set -e

echo "Applying database migrations..."
alembic upgrade head
echo "Migrations applied."

exec "$@"
