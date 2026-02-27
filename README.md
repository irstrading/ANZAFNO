# ANZA FNO Intelligence Platform - Windows Setup Guide

## Prerequisites

1.  **Python 3.11+**: [Download Python](https://www.python.org/downloads/windows/)
    *   Make sure to check "Add Python to PATH" during installation.
2.  **PostgreSQL**: [Download PostgreSQL](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)
    *   During installation, remember the password you set (default is usually `postgres`/`password`).
    *   **TimescaleDB**: Ideally install TimescaleDB extension. If not available, standard Postgres works but is slower for history.
3.  **Redis**: [Download Redis for Windows](https://github.com/microsoftarchive/redis/releases)
    *   Install the `.msi` file and ensure the service is running.

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <your-repo-url>
    cd anza-fno
    ```

2.  **Set up Virtual Environment**:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r backend/requirements.txt
    ```

4.  **Configure Environment**:
    *   Copy `.env.example` to `.env` in the `backend` folder.
    *   Open `backend/.env` and update your AngelOne credentials and DB password.
    ```bash
    copy backend\.env.example backend\.env
    ```

5.  **Initialize Database**:
    ```bash
    python backend/app/db/init_db.py
    ```

## Running the Platform

To make it easy, use the `run.bat` script (double-click it or run from terminal).

### Manual Startup

1.  **Start Redis Server** (if not running as service):
    ```bash
    redis-server
    ```

2.  **Start Backend API**:
    ```bash
    uvicorn backend.app.main:app --reload
    ```
    *   API Docs: http://localhost:8000/docs

3.  **Start Celery Worker** (for background tasks):
    ```bash
    celery -A backend.app.celery_app worker --loglevel=info -P solo
    ```
    *(Note: `-P solo` is required for Celery on Windows)*

4.  **Start Celery Beat** (for scheduled tasks):
    ```bash
    celery -A backend.app.celery_app beat --loglevel=info
    ```

## Project Structure

*   `backend/app/api`: API Endpoints (FastAPI)
*   `backend/app/engine`: Core Logic (Fetcher, Greeks, Analysis)
*   `backend/app/models`: Database Models
*   `backend/app/tasks.py`: Background Tasks
