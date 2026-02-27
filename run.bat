@echo off
echo Starting ANZA FNO Platform...

REM Activate Virtual Environment for Backend
call backend\venv\Scripts\activate

REM Start Redis (Optional check, assumes service is running)
REM start redis-server

REM Start Celery Worker (New Window)
start "Celery Worker" cmd /k "cd backend && ..\backend\venv\Scripts\activate && celery -A app.celery_app worker --loglevel=info -P solo"

REM Start Celery Beat (New Window)
start "Celery Beat" cmd /k "cd backend && ..\backend\venv\Scripts\activate && celery -A app.celery_app beat --loglevel=info"

REM Start FastAPI Backend (New Window)
start "Backend API" cmd /k "cd backend && ..\backend\venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Start Frontend (New Window)
start "Frontend Dashboard" cmd /k "cd frontend && npm run dev"

echo All services started!
pause
