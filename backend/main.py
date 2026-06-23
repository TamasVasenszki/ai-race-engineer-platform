from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai import get_provider
from config import settings
from routers import laps


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ai_provider = get_provider()
    yield


app = FastAPI(title="AI Race Engineer", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(laps.router, prefix="/laps", tags=["laps"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "ai_provider": settings.ai_provider}
