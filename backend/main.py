"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.game import router as game_router

app = FastAPI(title="Verdict AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # Dev-only: allow localhost and 127.0.0.1 on any port so Vite's
    # port-shifting (5173 → 5174 → …) never breaks the OPTIONS preflight.
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
