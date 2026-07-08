from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from ai import get_provider
from config import settings
from routers import laps, sessions


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
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])

# Prometheus metrics at /metrics (http_requests_total, http_request_duration_seconds, …),
# scraped by the kube-prometheus-stack via the ServiceMonitor in monitoring/.
Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "ai_provider": settings.ai_provider}
