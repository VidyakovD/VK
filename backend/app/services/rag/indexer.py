import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import KnowledgeBaseDocument
from app.services.llm.embeddings import get_embeddings_client
from app.services.rag.chunker import chunk_text
from app.services.rag.qdrant_service import collection_name_for_agent, get_qdrant_service

log = get_logger(__name__)


async def index_document(
    session: AsyncSession,
    document_id: uuid.UUID,
) -> int:
    """
    Take a KnowledgeBaseDocument row with content_text, chunk it,
    embed, upsert to Qdrant, update the row with chunks_count + indexed_at.
    Returns number of chunks indexed.
    """
    doc = await session.get(KnowledgeBaseDocument, document_id)
    if doc is None:
        raise ValueError(f"Document {document_id} not found")
    if not doc.content_text:
        raise ValueError(f"Document {document_id} has no content_text")

    chunks = chunk_text(doc.content_text)
    if not chunks:
        log.warning("index.empty_after_chunking", document=str(document_id))
        return 0

    embeddings = get_embeddings_client()
    qdrant = get_qdrant_service()

    # Batch embed (OpenAI handles arrays well)
    texts = [c.text for c in chunks]
    vectors = await embeddings.embed(texts)

    triples: list[tuple[str, list[float], int]] = [
        (c.text, v, c.index) for c, v in zip(chunks, vectors, strict=True)
    ]
    count = await qdrant.upsert_chunks(
        agent_id=doc.agent_id,
        document_id=doc.id,
        chunks=triples,
    )

    doc.chunks_count = count
    doc.qdrant_collection = collection_name_for_agent(doc.agent_id)
    doc.indexed_at = datetime.now(UTC)
    await session.flush()

    log.info("index.done", document=str(document_id), chunks=count)
    return count


async def delete_document_index(
    session: AsyncSession,
    document_id: uuid.UUID,
) -> None:
    """Remove document's chunks from Qdrant and delete the DB row."""
    doc = await session.get(KnowledgeBaseDocument, document_id)
    if doc is None:
        return
    qdrant = get_qdrant_service()
    await qdrant.delete_document(agent_id=doc.agent_id, document_id=doc.id)
    await session.delete(doc)
    await session.flush()


async def count_indexed_documents(session: AsyncSession, agent_id: uuid.UUID) -> int:
    """How many KB documents are indexed for an agent."""
    stmt = select(KnowledgeBaseDocument).where(KnowledgeBaseDocument.agent_id == agent_id)
    result = await session.execute(stmt)
    return len(result.scalars().all())
