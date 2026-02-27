# backend/app/main.py
from fastapi import FastAPI
from app.api import scanner, stock, auth, watchlist, websocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ANZA F&O Intelligence Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(scanner.router, prefix="/api/scanner", tags=["Scanner"])
app.include_router(stock.router, prefix="/api/stock", tags=["Stock"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["Watchlist"])
app.include_router(websocket.router)

@app.get("/")
async def root():
    return {"message": "ANZA F&O Intelligence Platform API is running"}
