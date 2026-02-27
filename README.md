# ANZA FNO Intelligence Platform

## Overview
Institutional-grade Indian F&O analysis platform with real-time data, advanced Greeks, and AI-driven insights.

## Prerequisites

1.  **Python 3.11+**: [Download Python](https://www.python.org/downloads/windows/)
2.  **Node.js 18+**: [Download Node.js](https://nodejs.org/en/download)
3.  **PostgreSQL**: [Download PostgreSQL](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)
4.  **Redis**: [Download Redis for Windows](https://github.com/microsoftarchive/redis/releases)

## Installation & Setup

### 1. Backend Setup
1.  Navigate to `backend` folder.
2.  Create virtual environment:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configure `.env` (copy from `.env.example`).
5.  Initialize Database:
    ```bash
    python app/db/init_db.py
    ```

### 2. Frontend Setup
1.  Navigate to `frontend` folder.
2.  Install dependencies:
    ```bash
    npm install
    ```

## Running the Platform

### Option A: One-Click Script (Windows)
Double-click `run.bat` in the root folder. This starts Redis (if needed), Celery Worker, Celery Beat, Backend API, and Frontend Dev Server.

### Option B: Manual Startup

**Terminal 1 (Backend):**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

**Terminal 3 (Celery Worker):**
```bash
cd backend
venv\Scripts\activate
celery -A app.celery_app worker --loglevel=info -P solo
```

**Terminal 4 (Celery Beat):**
```bash
cd backend
venv\Scripts\activate
celery -A app.celery_app beat --loglevel=info
```

## Access
- **Frontend Dashboard**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs
