#!/bin/bash
set -e

echo "=========================================="
echo "Bank-in-a-Box Startup"
echo "=========================================="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until pg_isready -h db -p 5432 -U ${POSTGRES_USER:-bank_user} > /dev/null 2>&1; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done
echo "✓ PostgreSQL is ready"

# Run Alembic migrations
echo "Running database migrations..."
python -m alembic upgrade head
if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully"
else
    echo "⚠️  Migration warning, but continuing..."
fi

echo "=========================================="
echo "Starting application..."
echo "=========================================="

# Execute the main command (passed as arguments)
exec "$@"

