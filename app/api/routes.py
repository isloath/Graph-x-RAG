from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_service
from app.models.schemas import (
    ApplicationIn,
    ApplicationListResponse,
    FraudRing,
    GraphResponse,
    IngestRequest,
    IngestResponse,
    RAGQueryRequest,
    RAGResponse,
    ResetResponse,
    RiskResult,
    SearchResult,
)
from app.services.fraud_platform_service import FraudPlatformService

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_data(
    request: IngestRequest,
    svc: FraudPlatformService = Depends(get_service),
) -> IngestResponse:
    return await svc.ingest(request)


@router.get("/applications", response_model=ApplicationListResponse)
async def list_applications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    svc: FraudPlatformService = Depends(get_service),
) -> ApplicationListResponse:
    return await svc.list_applications(page, page_size)


@router.get("/applications/{application_id}", response_model=ApplicationIn)
async def get_application(
    application_id: str,
    svc: FraudPlatformService = Depends(get_service),
) -> ApplicationIn:
    app = await svc.get_application(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app




@router.get("/applications/{application_id}/graph", response_model=GraphResponse)
async def application_graph(
    application_id: str,
    svc: FraudPlatformService = Depends(get_service),
) -> GraphResponse:
    try:
        return await svc.application_graph(application_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/risk/{application_id}", response_model=RiskResult)
async def compute_risk(
    application_id: str,
    svc: FraudPlatformService = Depends(get_service),
) -> RiskResult:
    app = await svc.get_application(application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return await svc.compute_risk(app)


@router.post("/communities/recompute")
async def recompute_communities(svc: FraudPlatformService = Depends(get_service)) -> dict[str, str]:
    await svc.recompute_communities()
    return {"status": "ok"}


@router.get("/fraud-rings", response_model=list[FraudRing])
async def list_fraud_rings(svc: FraudPlatformService = Depends(get_service)) -> list[FraudRing]:
    return await svc.list_fraud_rings()


@router.get("/semantic-search", response_model=list[SearchResult])
async def semantic_search(
    q: str,
    top_k: int = Query(default=5, ge=1, le=20),
    svc: FraudPlatformService = Depends(get_service),
) -> list[SearchResult]:
    return await svc.semantic_search(q, top_k)


@router.post("/rag-query", response_model=RAGResponse)
async def rag_query(
    payload: RAGQueryRequest,
    svc: FraudPlatformService = Depends(get_service),
) -> RAGResponse:
    return await svc.rag_query(payload.question, payload.top_k)


@router.post("/reset", response_model=ResetResponse)
async def reset_pipeline(svc: FraudPlatformService = Depends(get_service)) -> ResetResponse:
    await svc.reset()
    return ResetResponse(status="reset")
