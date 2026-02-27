@echo off
echo Starting ANZA FNO Platform...

REM Activate Virtual Environment
call venv\Scripts\activate

REM Start Redis (Optional check, assumes service is running)
REM start redis-server

REM Start Celery Worker (New Window)
start "Celery Worker" cmd /k "celery -A backend.app.celery_app worker --loglevel=info -P solo"

REM Start Celery Beat (New Window)
start "Celery Beat" cmd /k "celery -A backend.app.celery_app beat --loglevel=info"

REM Start FastAPI Backend
echo Starting API Server...
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

pause
