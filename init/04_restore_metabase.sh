#!/bin/bash
set -e
echo "==> Restaurando metabase_db desde dump..."
psql -U "$POSTGRES_USER" -d metabase_db -f /docker-entrypoint-initdb.d/03_metabase_dump.sql
echo "==> metabase_db restaurada exitosamente"