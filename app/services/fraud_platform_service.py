from __future__ import annotations

import logging

from app.models.schemas import (
    ApplicationIn,
    ApplicationListResponse,
    FraudRing,
    IngestRequest,
    IngestResponse,
    GraphEdge,
    GraphNode,
    GraphResponse,
    RAGResponse,
    RiskResult,
    SearchResult,
)
from app.repositories.graph_repository import GraphRepository
from app.repositories.vector_repository import VectorRepository
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService
from app.services.risk_service import RiskService

logger = logging.getLogger(__name__)


class FraudPlatformService:
    def __init__(
        self,
        graph_repo: GraphRepository,
        vector_repo: VectorRepository,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
        risk_service: RiskService,
    ) -> None:
        self.graph_repo = graph_repo
        self.vector_repo = vector_repo
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.risk_service = risk_service

    @staticmethod
    def summarize_application(app: ApplicationIn) -> str:
        return (
            f"Application {app.application_id} by customer {app.customer_id}, amount {app.loan_amount}, "
            f"status {app.status.value}, phone={app.phone}, email={app.email}, "
            f"document={app.document_id}, device={app.device_id}, account={app.bank_account}, wallet={app.wallet_id}."
        )

    async def bootstrap(self) -> None:
        await self.graph_repo.ensure_indexes()
        try:
            await self.vector_repo.ensure_collection()
        except Exception as exc:
            logger.warning("Vector DB bootstrap skipped/unavailable: %s", exc)

    async def ingest(self, req: IngestRequest) -> IngestResponse:
        ingested = await self.graph_repo.ingest_applications(req.applications)
        if req.applications:
            try:
                texts = [self.summarize_application(a) for a in req.applications]
                vectors = await self.embedding_service.embed_batch(texts)
                points = [
                    {
                        "id": app.application_id,
                        "vector": vector,
                        "payload": {
                            "type": "application",
                            "application_id": app.application_id,
                            "summary": text,
                        },
                    }
                    for app, vector, text in zip(req.applications, vectors, texts, strict=True)
                ]
                await self.vector_repo.upsert(points)
            except Exception as exc:
                logger.warning("Vector indexing failed for this ingest batch; graph ingest succeeded: %s", exc)
        return IngestResponse(ingested=ingested)

    async def list_applications(self, page: int, page_size: int) -> ApplicationListResponse:
        rows, total = await self.graph_repo.list_applications(page, page_size)
        items = [
            ApplicationIn(
                application_id=row["application_id"],
                customer_id=row.get("customer_id", ""),
                created_at=row["created_at"].to_native(),
                phone=row.get("phone"),
                email=row.get("email"),
                document_id=row.get("document_id"),
                device_id=row.get("device_id"),
                bank_account=row.get("bank_account"),
                wallet_id=row.get("wallet_id"),
                loan_amount=row.get("loan_amount", 0),
                status=row.get("status", "approved"),
            )
            for row in rows
        ]
        return ApplicationListResponse(items=items, page=page, page_size=page_size, total=total)

    async def get_application(self, application_id: str) -> ApplicationIn | None:
        row = await self.graph_repo.get_application(application_id)
        if not row:
            return None
        return ApplicationIn(
            application_id=row["application_id"],
            customer_id=row.get("customer_id", ""),
            created_at=row["created_at"].to_native(),
            phone=row.get("phone"),
            email=row.get("email"),
            document_id=row.get("document_id"),
            device_id=row.get("device_id"),
            bank_account=row.get("bank_account"),
            wallet_id=row.get("wallet_id"),
            loan_amount=row.get("loan_amount", 0),
            status=row.get("status", "approved"),
        )

    async def compute_risk(self, app: ApplicationIn) -> RiskResult:
        phone_degree = await self.graph_repo.identifier_degree("Phone", app.phone) if app.phone else 0
        document_degree = (
            await self.graph_repo.identifier_degree("Document", app.document_id) if app.document_id else 0
        )
        device_degree = await self.graph_repo.identifier_degree("Device", app.device_id) if app.device_id else 0

        candidates = [phone_degree, document_degree, device_degree]
        max_identifier_degree = max(candidates) if candidates else 0
        _, community_size = await self.graph_repo.get_community(app.application_id)

        return await self.risk_service.score(
            app.application_id,
            phone_degree,
            document_degree,
            device_degree,
            max_identifier_degree,
            community_size,
        )

    async def recompute_communities(self) -> None:
        await self.graph_repo.run_louvain()

    async def list_fraud_rings(self) -> list[FraudRing]:
        rings = await self.graph_repo.list_fraud_rings(min_size=5)
        return [FraudRing(**ring) for ring in rings]


    async def application_graph(self, application_id: str) -> GraphResponse:
        app = await self.get_application(application_id)
        if not app:
            raise ValueError("Application not found")
        graph = await self.graph_repo.graph_view_for_application(application_id, hops=2)
        return GraphResponse(
            application_id=application_id,
            nodes=[GraphNode(**node) for node in graph["nodes"]],
            edges=[GraphEdge(**edge) for edge in graph["edges"]],
        )

    async def semantic_search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        vector = await self.embedding_service.embed(query)
        rows = await self.vector_repo.search(vector, limit=top_k)
        return [SearchResult(**r) for r in rows]

    async def rag_query(self, question: str, top_k: int = 5) -> RAGResponse:
        hits = await self.semantic_search(question, top_k)
        contexts: list[str] = []
        evidence: list[str] = []

        for hit in hits:
            payload = hit.payload
            summary = payload.get("summary", "")
            app_id = payload.get("application_id")
            if summary:
                contexts.append(summary)
                evidence.append(f"vector:{hit.id}")
            if app_id:
                expansions = await self.graph_repo.subgraph_for_application(app_id, hops=2)
                contexts.extend(expansions)
                evidence.append(f"graph:{app_id}")

        if not contexts:
            answer = "I cannot determine the answer from retrieved evidence."
        else:
            answer = await self.llm_service.answer(question, contexts)

        return RAGResponse(question=question, answer=answer, evidence=evidence)

    async def reset(self) -> None:
        await self.graph_repo.reset()
        try:
            await self.vector_repo.reset()
        except Exception as exc:
            logger.warning("Vector reset skipped/unavailable: %s", exc)
