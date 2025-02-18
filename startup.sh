#!/bin/bash

echo "Starting Azure App Service deployment process"

# Create necessary directories in writable location
echo "Creating necessary directories..."
mkdir -p /home/data/instance
mkdir -p /home/data/uploads
chmod -R 777 /home/data/instance
chmod -R 777 /home/data/uploads

# Create and activate virtual environment
if [ ! -d "/home/antenv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv /home/antenv
fi

echo "Activating virtual environment"
source /home/antenv/bin/activate

# Upgrade pip and install dependencies
echo "Upgrading pip"
pip install --upgrade pip

if [ -f "/home/site/wwwroot/requirements.txt" ]; then
    echo "Installing dependencies"
    pip install -r /home/site/wwwroot/requirements.txt || { echo "Dependency installation failed"; exit 1; }
else
    echo "requirements.txt not found!"
    exit 1
fi

# Initialize database
echo "Initializing database..."
python << EOF
import os
import sys
sys.path.append('/home/site/wwwroot')
from app import initialize_database
if not initialize_database():
    print("Database initialization failed")
    sys.exit(1)
EOF

# Apply migrations if they exist
if [ -d "/home/site/wwwroot/migrations" ]; then
    echo "Applying database migrations"
    cd /home/site/wwwroot
    export FLASK_APP=app.py
    flask db upgrade || { echo "Migration failed"; exit 1; }
fi

# Verify database permissions
if [ -f "/home/data/instance/site.db" ]; then
    echo "Setting database file permissions..."
    chmod 666 /home/data/instance/site.db
fi

# Start Gunicorn with proper path
echo "Starting Gunicorn..."
cd /home/site/wwwroot
gunicorn --bind=0.0.0.0 --timeout 600 --workers=4 app:app --log-level debug
