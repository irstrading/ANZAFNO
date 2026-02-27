# 🔥 ANZA FNO Intelligence Platform

Advanced F&O Trading Intelligence Platform for the Indian Market (NSE). Built for high-frequency data processing, quantitative Greek analysis, and Smart Money flow tracking using the AngelOne SmartAPI.

## 🚀 Key Features

- **Vectorized Greeks Engine**: Black-76 model for Delta, Gamma, Vega, Theta, Vanna, and Charm.
- **Dealer Exposure (GEX)**: Real-time tracking of Gamma, Delta, Vanna, and Charm exposure.
- **Intelligence Layer**: Automated detection of trade structures (Naked vs. Spreads) and OI Velocity signals.
- **Smart Money Verdict**: Composite scoring system providing actionable BUY/SELL setups.
- **Live Dashboard**: Bloomberg-style 'Dark Terminal' React frontend with real-time updates.
- **Alert System**: Telegram bot for instant signals and regime changes.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, Celery, Redis.
- **Database**: TimescaleDB (Time-series optimized PostgreSQL).
- **Frontend**: React 18, Vite, TailwindCSS, Zustand, Recharts.
- **Broker**: AngelOne SmartAPI (REST + WebSocket).
- **Infrastructure**: Docker Compose.

---

## 📦 Installation & Setup

### 1. Prerequisites
Ensure you have the following installed:
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)

### 2. Clone the Repository
```bash
git clone <your-repo-url>
cd anza-fno
```

### 3. Configure Environment Variables
Copy the example environment file and fill in your credentials:
```bash
cp .env.example .env
```
Open `.env` and provide your:
- **AngelOne**: `API_KEY`, `CLIENT_ID`, `PASSWORD`, `TOTP_SECRET`.
- **Telegram**: `BOT_TOKEN`, `CHAT_ID`.
- **Database**: Set a strong `DB_PASSWORD`.

### 4. Start the Platform
Launch all 7 services with a single command:
```bash
docker-compose up -d
```

---

## 🖥️ Usage & Access

Once the containers are up and running, you can access the platform at the following URLs:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend Dashboard** | [http://localhost:3000](http://localhost:3000) | Main trading dashboard |
| **Backend API** | [http://localhost:8000](http://localhost:8000) | FastAPI REST endpoints |
| **API Documentation** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger UI docs |
| **TimescaleDB** | `localhost:5432` | PostgreSQL database access |
| **Redis** | `localhost:6379` | Real-time cache access |

---

## 📂 Project Structure

- `backend/app/core`: The quantitative "brain" (Greeks, GEX, signals).
- `backend/app/brokers`: Market data adapters (AngelOne REST & WS).
- `backend/app/tasks`: Background workers for stock scanning and analysis.
- `frontend/src/pages`: Interactive dashboard pages (Scanner, NiftyDesk, Watchlist).

---

## ⚠️ Disclaimer
This software is for educational and research purposes only. Trading in F&O involves significant risk. Always verify signals and consult with a financial advisor before making investment decisions.

**Built for Maximum Edge.**
