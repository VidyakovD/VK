import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.db import get_session
from app.core.logging import get_logger
from app.models import AgentConversation, User
from app.schemas import ChatRequest, ChatResponse, ChatSource
from app.services import agent_service, billing_service
from app.services.llm.base import LLMMessage
from app.services.rag import generate_rag_answer

log = get_logger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_agent(
    agent_id: uuid.UUID,
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """
    Test chat with an agent from the Mini App.
    Runs the RAG pipeline, debits credits, persists conversation log.
    """
    try:
        agent = await agent_service.assert_user_owns_agent(session, current_user, agent_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    history = [LLMMessage(role=m.role, content=m.content) for m in body.history]

    answer = await generate_rag_answer(
        session=session,
        agent=agent,
        user_question=body.message,
        history=history,
        top_k=body.top_k,
    )

    # Billing — debit AFTER successful LLM call.
    cost = await billing_service.cost_for_llm_call(
        session,
        provider=answer.provider,
        tokens_in=answer.tokens_in,
        tokens_out=answer.tokens_out,
    )
    try:
        await billing_service.debit_credits(
            session=session,
            user=current_user,
            amount=cost,
            resource_type="llm_request",
            description=f"Agent {agent.name} ({answer.provider}/{answer.model})",
            resource_id=agent.id,
        )
    except billing_service.InsufficientCredits as exc:
        # We still return the answer the user just paid for cognitively —
        # but bills won't accumulate further. Mark as 402-ish via header would be
        # ideal; for MVP, just log a warning and return the answer.
        log.warning(
            "billing.insufficient_after_call",
            user=str(current_user.id),
            cost=str(cost),
            balance=str(current_user.credits_balance),
            error=str(exc),
        )

    # Persist conversation log (subscriber_id NULL for test-chat from owner)
    now = datetime.now(UTC).isoformat()
    convo = AgentConversation(
        agent_id=agent.id,
        subscriber_id=None,
        messages=[
            *[m.model_dump() for m in body.history],
            {"role": "user", "content": body.message, "timestamp": now},
            {"role": "assistant", "content": answer.text, "timestamp": now},
        ],
        tokens_in=answer.tokens_in,
        tokens_out=answer.tokens_out,
        credits_spent=cost,
        status="active",
    )
    session.add(convo)
    await session.flush()
    convo_id = convo.id

    return ChatResponse(
        text=answer.text,
        sources=[
            ChatSource(
                text=c.text,
                score=c.score,
                document_id=c.document_id,
                chunk_index=c.chunk_index,
            )
            for c in answer.sources
        ],
        confidence=answer.confidence,
        tokens_in=answer.tokens_in,
        tokens_out=answer.tokens_out,
        credits_spent=cost,
        model=answer.model,
        provider=answer.provider,
        fallback_triggered=answer.fallback_triggered,
        conversation_id=convo_id,
    )
