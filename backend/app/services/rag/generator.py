import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import AIAgent
from app.services.llm import LLMMessage, LLMResponse, get_anthropic_client, get_openai_client
from app.services.rag.retriever import RetrievedChunk, retrieve

log = get_logger(__name__)

# Trim history to last N user/assistant turns to control context size.
HISTORY_TURNS_LIMIT = 6


@dataclass
class RAGAnswer:
    text: str
    sources: list[RetrievedChunk]
    confidence: float          # max similarity score across retrieved chunks (0..1)
    tokens_in: int
    tokens_out: int
    model: str
    provider: str
    fallback_triggered: bool   # True if confidence below threshold


_DEFAULT_RU_SYSTEM_HEADER = (
    "Ты — ИИ-консультант сообщества. Отвечай только на основе предоставленного контекста ниже. "
    "Если в контексте нет ответа на вопрос пользователя — честно скажи, что не знаешь, "
    "и предложи связаться с менеджером. Не выдумывай факты, цены, условия."
)


def build_rag_prompt(
    agent: AIAgent,
    chunks: list[RetrievedChunk],
    history: list[LLMMessage],
    user_question: str,
) -> list[LLMMessage]:
    """Compose system + context + recent history + question into a message list."""
    context_blocks = "\n\n".join(
        f"[Источник {i+1}, релевантность {c.score:.2f}]\n{c.text}"
        for i, c in enumerate(chunks)
    )
    system_parts = [_DEFAULT_RU_SYSTEM_HEADER]
    if agent.system_prompt:
        system_parts.append(agent.system_prompt)
    if agent.tone:
        system_parts.append(f"Тон общения: {agent.tone}")
    system_parts.append("---\nКонтекст из базы знаний:\n" + (context_blocks or "(пусто)"))
    system_msg = LLMMessage(role="system", content="\n\n".join(system_parts))

    # Keep only the last N turns of the history to stay within budget.
    trimmed_history = history[-HISTORY_TURNS_LIMIT * 2 :]

    return [system_msg, *trimmed_history, LLMMessage(role="user", content=user_question)]


async def generate_rag_answer(
    session: AsyncSession,
    agent: AIAgent,
    user_question: str,
    history: list[LLMMessage] | None = None,
    top_k: int = 5,
) -> RAGAnswer:
    """End-to-end RAG: retrieve → assemble prompt → call LLM → return structured answer."""
    history = history or []

    chunks = await retrieve(agent.id, user_question, top_k=top_k)
    confidence = max((c.score for c in chunks), default=0.0)

    messages = build_rag_prompt(agent, chunks, history, user_question)

    # Provider selection — agent.llm_provider determines which client.
    if agent.llm_provider == "anthropic":
        client = get_anthropic_client()
    else:
        client = get_openai_client()

    response: LLMResponse = await client.chat(
        messages=messages,
        model=agent.llm_model or None,
        temperature=float(agent.temperature),
    )

    fallback = confidence < float(agent.confidence_threshold)
    if fallback:
        log.info(
            "rag.confidence_below_threshold",
            agent=str(agent.id),
            confidence=confidence,
            threshold=float(agent.confidence_threshold),
        )

    return RAGAnswer(
        text=response.text,
        sources=chunks,
        confidence=confidence,
        tokens_in=response.tokens_in,
        tokens_out=response.tokens_out,
        model=response.model,
        provider=response.provider,
        fallback_triggered=fallback,
    )
