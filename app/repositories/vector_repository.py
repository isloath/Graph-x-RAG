from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class VectorRepository:
    def __init__(self, host: str, port: int, collection: str, vector_size: int) -> None:
        self.collection = collection
        self.client = QdrantClient(host=host, port=port)
        self.vector_size = vector_size

    async def ensure_collection(self) -> None:
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

    async def reset(self) -> None:
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        await self.ensure_collection()

    async def upsert(self, points: list[dict[str, Any]]) -> None:
        qdrant_points = [
            PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
            for p in points
        ]
        if qdrant_points:
            self.client.upsert(collection_name=self.collection, points=qdrant_points)

    async def search(self, vector: list[float], limit: int = 5) -> list[dict[str, Any]]:
        res = self.client.search(collection_name=self.collection, query_vector=vector, limit=limit)
        return [
            {"id": str(r.id), "score": float(r.score), "payload": r.payload or {}}
            for r in res
        ]
