import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from ai import get_provider
from ai.ollama import OllamaProvider
from config import settings
from routers import incidents, laps, sessions
from ws import ConnectionManager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ai_provider = get_provider()
    app.state.ws_manager = ConnectionManager()
    app.state.ollama_status = None
    if isinstance(app.state.ai_provider, OllamaProvider):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{settings.ollama_base_url}/api/tags")
                r.raise_for_status()
                app.state.ollama_status = "ok"
                logger.info("Ollama reachable at %s", settings.ollama_base_url)
        except Exception:
            app.state.ollama_status = "unreachable"
            logger.warning(
                "Ollama unreachable at %s — requests will fail until it's available",
                settings.ollama_base_url,
            )
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
app.include_router(incidents.router, prefix="/sessions", tags=["incidents"])

# Prometheus metrics at /metrics (http_requests_total, http_request_duration_seconds, …),
# scraped by the kube-prometheus-stack via the ServiceMonitor in monitoring/.
Instrumentator().instrument(app).expose(app)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    manager: ConnectionManager = websocket.app.state.ws_manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/health")
async def health(request: Request) -> dict:
    result: dict = {"status": "ok", "ai_provider": settings.ai_provider}
    if request.app.state.ollama_status is not None:
        result["ollama_status"] = request.app.state.ollama_status
    return result
