#!/bin/sh
# Railway injects PORT at runtime; default to 8000 for local Docker
PORT="${PORT:-8000}"
echo "Starting CloudSaviour on port $PORT"
exec uvicorn app.service:app --host 0.0.0.0 --port "$PORT"
