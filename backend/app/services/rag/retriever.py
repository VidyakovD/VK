import uuid
from dataclasses import dataclass

from app.core.logging import get_logger
from app.services.llm.embeddings import get_embeddings_client
from app.services.rag.qdrant_service import get_qdrant_service

log = get_logger(__name__)


@dataclass
class RetrievedChunk:
    text: str
    score: float
    document_id: str
    chunk_index: int


async def retrieve(agent_id: uuid.UUID, query: str, top_k: int = 5) -> list[RetrievedChunk]:
    """Embed the query, search Qdrant, return ranked chunks with similarity scores."""
    embeddings = get_embeddings_client()
    qdrant = get_qdrant_service()

    qvec = await embeddings.embed_one(query)
    points = await qdrant.search(agent_id, qvec, top_k=top_k)

    chunks = [
        RetrievedChunk(
            text=str(p.payload.get("text", "")) if p.payload else "",
            score=float(p.score),
            document_id=str(p.payload.get("document_id", "")) if p.payload else "",
            chunk_index=int(p.payload.get("chunk_index", 0)) if p.payload else 0,
        )
        for p in points
    ]
    log.info("rag.retrieve", agent=str(agent_id), top_k=top_k, found=len(chunks))
    return chunks
