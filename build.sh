#!/bin/bash

# Build script for Render deployment
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate --noinput

# Create superuser if it doesn't exist (optional)
# python manage.py createsuperuser --noinput --username admin --email admin@publicbridge.com || true --password admin