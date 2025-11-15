#!/bin/bash
# Set default port if not provided by Render
export PORT=${PORT:-10000}

echo "=== Render Deployment Debug Info ==="
echo "PORT environment variable: $PORT"
echo "Binding to: 0.0.0.0:$PORT"
echo "=== Starting Application ==="

# Run database migrations before starting the application
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Wait for any previous services to release the port
echo "Initializing port binding..."
sleep 2

# Use Gunicorn with Uvicorn worker for better reliability
echo "Starting Gunicorn with Uvicorn worker on 0.0.0.0:$PORT..."
exec gunicorn PublicBridge.asgi:application \
  --bind 0.0.0.0:$PORT \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 1 \
  --timeout 120 \
  --keep-alive 2 \
  --log-level debug