from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.dependencies import get_service
from app.api.routes import router
from app.core.settings import settings

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Log registered routes so we can confirm /api/v1/ingest exists (debug 404)
    for route in app.routes:
        if hasattr(route, "path"):
            methods = getattr(route, "methods", None) or set()
            if methods:
                logger.info("Route: %s %s", ",".join(sorted(methods)), route.path)
    service = get_service()
    await service.bootstrap()
    yield
    service.graph_repo.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan, redirect_slashes=True)
app.include_router(router, prefix="/api/v1", tags=["fraud"])


@app.get("/api/v1", tags=["fraud"])
@app.get("/api/v1/", tags=["fraud"])
async def api_v1_root() -> dict:
    """Always on main app so /api/v1 and /api/v1/ never 404."""
    return {
        "message": "Graph RAG Fraud API v1",
        "ingest": "POST /api/v1/ingest",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(404)
async def not_found_handler(request: Request, _: Exception) -> JSONResponse:
    """Hint when 404: use no trailing slash (e.g. POST /api/v1/ingest)."""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Not Found",
            "path": str(request.url.path),
            "hint": "Use exact path without trailing slash, e.g. POST http://localhost:8000/api/v1/ingest",
        },
    )
