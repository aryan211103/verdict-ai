"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.game import router as game_router

app = FastAPI(title="Verdict AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
