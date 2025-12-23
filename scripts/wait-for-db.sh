#!/bin/bash

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! nc -z timescale 5432; do
  sleep 1
done
echo "Database is ready!"

# Run Alembic migrations
echo "Running Alembic migrations..."
if alembic upgrade head; then
  echo "Migrations completed successfully!"
else
  echo "Migration failed! Exiting."
  exit 1
fi

# Execute the main command
exec "$@"
