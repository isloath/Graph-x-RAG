from contextlib import asynccontextmanager

from fastapi import FastAPI

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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
