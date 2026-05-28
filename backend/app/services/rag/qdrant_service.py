import uuid
from functools import lru_cache

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from app.core.config import settings
from app.core.logging import get_logger
from app.services.llm.embeddings import get_embeddings_client

log = get_logger(__name__)


def collection_name_for_agent(agent_id: uuid.UUID) -> str:
    return f"agent_{agent_id.hex}"


class QdrantService:
    def __init__(self, client: AsyncQdrantClient) -> None:
        self._client = client

    async def ensure_collection(self, agent_id: uuid.UUID) -> str:
        name = collection_name_for_agent(agent_id)
        embeddings = get_embeddings_client()

        existing = await self._client.collection_exists(collection_name=name)
        if existing:
            return name

        await self._client.create_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(
                size=embeddings.dimensions,
                distance=qmodels.Distance.COSINE,
            ),
        )
        # Payload index for document_id so we can delete a document's chunks fast
        await self._client.create_payload_index(
            collection_name=name,
            field_name="document_id",
            field_schema=qmodels.PayloadSchemaType.KEYWORD,
        )
        log.info("qdrant.collection.created", name=name, dim=embeddings.dimensions)
        return name

    async def upsert_chunks(
        self,
        agent_id: uuid.UUID,
        document_id: uuid.UUID,
        chunks: list[tuple[str, list[float], int]],
    ) -> int:
        """
        chunks: list of (text, embedding, index)
        Returns number of points upserted.
        """
        if not chunks:
            return 0
        name = await self.ensure_collection(agent_id)
        points = [
            qmodels.PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "document_id": str(document_id),
                    "chunk_index": index,
                    "text": text,
                },
            )
            for text, embedding, index in chunks
        ]
        await self._client.upsert(collection_name=name, points=points, wait=True)
        log.info("qdrant.upsert", agent=str(agent_id), document=str(document_id), count=len(points))
        return len(points)

    async def search(
        self,
        agent_id: uuid.UUID,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[qmodels.ScoredPoint]:
        name = collection_name_for_agent(agent_id)
        if not await self._client.collection_exists(collection_name=name):
            return []
        result = await self._client.query_points(
            collection_name=name,
            query=query_embedding,
            limit=top_k,
            with_payload=True,
        )
        return list(result.points)

    async def delete_document(self, agent_id: uuid.UUID, document_id: uuid.UUID) -> int:
        name = collection_name_for_agent(agent_id)
        if not await self._client.collection_exists(collection_name=name):
            return 0
        await self._client.delete(
            collection_name=name,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="document_id",
                            match=qmodels.MatchValue(value=str(document_id)),
                        )
                    ]
                )
            ),
        )
        log.info("qdrant.delete_document", agent=str(agent_id), document=str(document_id))
        return 1

    async def drop_collection(self, agent_id: uuid.UUID) -> None:
        name = collection_name_for_agent(agent_id)
        if await self._client.collection_exists(collection_name=name):
            await self._client.delete_collection(collection_name=name)
            log.info("qdrant.collection.dropped", name=name)


@lru_cache(maxsize=1)
def get_qdrant_service() -> QdrantService:
    client = AsyncQdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )
    return QdrantService(client)
