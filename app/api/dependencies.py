from functools import lru_cache

from app.core.settings import settings
from app.repositories.graph_repository import GraphRepository
from app.repositories.vector_repository import VectorRepository
from app.services.embedding_service import EmbeddingService
from app.services.fraud_platform_service import FraudPlatformService
from app.services.llm_service import LLMService
from app.services.risk_service import RiskService


@lru_cache
def get_service() -> FraudPlatformService:
    return FraudPlatformService(
        graph_repo=GraphRepository(settings.memgraph_uri, settings.memgraph_user, settings.memgraph_password),
        vector_repo=VectorRepository(
            settings.qdrant_host,
            settings.qdrant_port,
            settings.qdrant_collection,
            settings.qdrant_vector_size,
        ),
        embedding_service=EmbeddingService(settings.embedding_model),
        llm_service=LLMService(settings.ollama_url, settings.ollama_model),
        risk_service=RiskService(),
    )
