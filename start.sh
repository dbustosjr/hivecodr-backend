#!/bin/bash
set -e

# Railway sets PORT environment variable
# Default to 8000 for local development
PORT=${PORT:-8000}

echo "Starting uvicorn on port $PORT"
exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
