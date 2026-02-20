from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.dependencies import get_service
from app.api.routes import router
from app.core.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    service = get_service()
    await service.bootstrap()
    yield
    service.graph_repo.close()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(router, prefix="/api/v1", tags=["fraud"])

web_dir = Path(__file__).resolve().parent / "web"
app.mount("/web", StaticFiles(directory=web_dir), name="web")


@app.get("/")
async def dashboard() -> FileResponse:
    return FileResponse(web_dir / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
