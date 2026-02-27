#!/bin/bash

# ANZA FNO Intelligence Platform - Production Startup Script
# Usage: ./start_prod.sh

echo "🚀 Starting ANZA FNO Intelligence Platform (Production Mode)..."

# 1. Check Dependencies
echo "Checking dependencies..."
if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis is not installed. Please install Redis."
    exit 1
fi
if ! command -v psql &> /dev/null; then
    echo "⚠️ PostgreSQL client not found (psql). Ensure DB is running."
fi

# 2. Start Redis (if not running)
if ! pgrep redis-server > /dev/null; then
    echo "Starting Redis..."
    redis-server --daemonize yes
else
    echo "✅ Redis is running."
fi

# 3. Environment Setup
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
export ENVIRONMENT=production

# 4. Database Initialization
echo "Initializing Database..."
# Run a python script to init DB tables
python3 -c "from backend.app.db.timescale import db_manager; db_manager.init_db()" || { echo "❌ DB Init Failed"; exit 1; }

# 5. Start Backend (Gunicorn/Uvicorn)
echo "Starting Backend API (Port 8000)..."
nohup uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4 > backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started with PID $BACKEND_PID"

# 6. Start Celery Worker
echo "Starting Celery Worker..."
nohup celery -A backend.app.tasks.celery_app worker --loglevel=info --concurrency=4 > celery_worker.log 2>&1 &
WORKER_PID=$!
echo "✅ Celery Worker started with PID $WORKER_PID"

# 7. Start Celery Beat (Scheduler)
echo "Starting Celery Beat..."
nohup celery -A backend.app.tasks.celery_app beat --loglevel=info > celery_beat.log 2>&1 &
BEAT_PID=$!
echo "✅ Celery Beat started with PID $BEAT_PID"

echo "🎉 All services started!"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo "   - Logs: backend.log, celery_worker.log, celery_beat.log"
echo ""
echo "To stop all services: kill $BACKEND_PID $WORKER_PID $BEAT_PID"
