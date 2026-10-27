import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from app.agents.executor import RetrievalExecutor
from app.agents.graph import WebScout
from app.core.config import Settings
from app.core.security import URLGuard
from app.evaluation.schemas import Answer, Query
from app.llm.factory import LLMRouter
from app.tools.http_browser import HTTPBrowser
from app.tools.playwright_browser import PlaywrightBrowser
from app.tools.search import SearchDiscovery
from app.tools.tinyfish import TinyFish


def build_engine(settings, client):
    guard = URLGuard()
    tiny = TinyFish(client, guard, settings) if settings.key("tinyfish") else None
    browser = PlaywrightBrowser(guard, settings) if settings.playwright_enabled else None
    executor = RetrievalExecutor(HTTPBrowser(client, guard, settings), tiny, browser, settings)
    return WebScout(settings, executor, SearchDiscovery(tiny), LLMRouter(settings, client), guard)


def create_app(engine=None):
    @asynccontextmanager
    async def lifespan(app):
        settings = Settings()
        # Ignore host proxy environment variables; use explicit egress policy in deployment.
        async with httpx.AsyncClient(trust_env=False, limits=httpx.Limits(max_connections=10),
                headers={"User-Agent": "WebScoutAI/0.1 (read-only research)"}) as client:
            app.state.engine = engine or build_engine(settings, client)
            app.state.capacity = asyncio.Semaphore(2)
            yield

    app = FastAPI(title="WebScout AI", version="0.1.0", lifespan=lifespan)

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse(status_code=422, content=Answer(question="", status="invalid_request",
            warnings=["Invalid request; question is required and fields must match /docs"]).model_dump(mode="json"))

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "webscout-ai", "amd_compatibility": "unverified"}

    @app.get("/ready")
    async def ready(request: Request):
        engine = request.app.state.engine
        eligible = engine.llm.candidates() if hasattr(engine.llm, "candidates") else []
        return {"status": "configured" if eligible else "missing_llm_configuration",
                "eligible_llm_providers": [n for n, _ in eligible],
                "live_integrations_validated": False}

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    @app.post("/query", response_model=Answer)
    async def query(payload: Query, request: Request):
        # No unbounded API queue; a third simultaneous job fails fast.
        capacity = request.app.state.capacity
        if capacity.locked():
            return JSONResponse(status_code=503, content=Answer(question=payload.question,
                status="retrieval_failed", warnings=["Server busy; retry later"]).model_dump(mode="json"))
        async with capacity:
            return await request.app.state.engine.answer(payload)

    return app


app = create_app()
