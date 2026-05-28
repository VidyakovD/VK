import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.db import get_session
from app.models import KnowledgeBaseDocument, User
from app.schemas import (
    AgentCreate,
    AgentRead,
    AgentUpdate,
    DocumentRead,
    DocumentUploadFromURL,
    DocumentUploadManual,
)
from app.schemas.common import OkResponse
from app.services import agent_service
from app.services.rag import (
    SUPPORTED_EXTENSIONS,
    delete_document_index,
    index_document,
    parse_document_bytes,
    parse_url,
)

router = APIRouter(prefix="/agents", tags=["agents"])


# --- Agent CRUD --------------------------------------------------------------
@router.get("", response_model=list[AgentRead])
async def list_agents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[AgentRead]:
    agents = await agent_service.list_agents_for_user(session, current_user)
    return [AgentRead.model_validate(a) for a in agents]


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: AgentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AgentRead:
    try:
        agent = await agent_service.create_agent(session, current_user, body)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return AgentRead.model_validate(agent)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AgentRead:
    try:
        agent = await agent_service.assert_user_owns_agent(session, current_user, agent_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AgentRead.model_validate(agent)


@router.put("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: uuid.UUID,
    body: AgentUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> AgentRead:
    try:
        agent = await agent_service.update_agent(session, current_user, agent_id, body)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AgentRead.model_validate(agent)


@router.delete("/{agent_id}", response_model=OkResponse)
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OkResponse:
    try:
        agent = await agent_service.assert_user_owns_agent(session, current_user, agent_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    # Drop Qdrant collection alongside DB cascade
    from app.services.rag import get_qdrant_service

    await get_qdrant_service().drop_collection(agent.id)
    await session.delete(agent)
    return OkResponse()


# --- Knowledge base ----------------------------------------------------------
MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB


@router.get("/{agent_id}/knowledge", response_model=list[DocumentRead])
async def list_kb(
    agent_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[DocumentRead]:
    try:
        docs = await agent_service.list_documents(session, current_user, agent_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [DocumentRead.model_validate(d) for d in docs]


@router.post("/{agent_id}/knowledge/file", response_model=DocumentRead)
async def upload_file(
    agent_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentRead:
    try:
        await agent_service.assert_user_owns_agent(session, current_user, agent_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    raw = await file.read()
    if len(raw) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {MAX_FILE_BYTES // (1024 * 1024)} MB",
        )

    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported extension {ext}. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    try:
        text = parse_document_bytes(raw, file.filename or "upload")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse document: {exc}",
        ) from exc

    doc = KnowledgeBaseDocument(
        agent_id=agent_id,
        source_type="file",
        file_name=file.filename,
        file_size=len(raw),
        content_text=text,
    )
    session.add(doc)
    await session.flush()
    await index_document(session, doc.id)
    return DocumentRead.model_validate(doc)


@router.post("/{agent_id}/knowledge/url", response_model=DocumentRead)
async def upload_url(
    agent_id: uuid.UUID,
    body: DocumentUploadFromURL,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentRead:
    try:
        await agent_service.assert_user_owns_agent(session, current_user, agent_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    try:
        text = await parse_url(body.url)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch/parse URL: {exc}",
        ) from exc

    doc = KnowledgeBaseDocument(
        agent_id=agent_id,
        source_type="url",
        source_url=body.url,
        content_text=text,
    )
    session.add(doc)
    await session.flush()
    await index_document(session, doc.id)
    return DocumentRead.model_validate(doc)


@router.post("/{agent_id}/knowledge/manual", response_model=DocumentRead)
async def upload_manual(
    agent_id: uuid.UUID,
    body: DocumentUploadManual,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentRead:
    try:
        await agent_service.assert_user_owns_agent(session, current_user, agent_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    doc = KnowledgeBaseDocument(
        agent_id=agent_id,
        source_type="manual",
        file_name=body.title,
        content_text=body.content_text,
    )
    session.add(doc)
    await session.flush()
    await index_document(session, doc.id)
    return DocumentRead.model_validate(doc)


@router.delete("/{agent_id}/knowledge/{doc_id}", response_model=OkResponse)
async def delete_kb_document(
    agent_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OkResponse:
    try:
        await agent_service.assert_user_owns_agent(session, current_user, agent_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    doc = await session.get(KnowledgeBaseDocument, doc_id)
    if doc is None or doc.agent_id != agent_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await delete_document_index(session, doc_id)
    return OkResponse()


# Chat endpoint lives in routes/chat.py
__all__ = ["router"]
