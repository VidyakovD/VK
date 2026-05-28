import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPKMixin


class AIAgent(Base, UUIDPKMixin):
    """ИИ-агент, привязанный к сообществу клиента."""

    __tablename__ = "ai_agents"

    community_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # 'consultant', 'sales', 'lead_qualifier', 'support'
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text)
    tone: Mapped[str | None] = mapped_column(String(50))
    # 'openai', 'anthropic'
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="openai")
    llm_model: Mapped[str | None] = mapped_column(String(100))
    temperature: Mapped[Decimal] = mapped_column(
        Numeric(2, 1), nullable=False, default=Decimal("0.7")
    )
    confidence_threshold: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.6")
    )
    # 'transfer_operator', 'static_message'
    fallback_action: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    community: Mapped["Community"] = relationship(back_populates="ai_agents")  # noqa: F821
    documents: Mapped[list["KnowledgeBaseDocument"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["AgentConversation"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )


class KnowledgeBaseDocument(Base, UUIDPKMixin):
    """Документ базы знаний — источник для RAG."""

    __tablename__ = "knowledge_base_documents"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 'file', 'url', 'manual', 'wall_post'
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_size: Mapped[int | None] = mapped_column(Integer)
    content_text: Mapped[str | None] = mapped_column(Text)
    chunks_count: Mapped[int | None] = mapped_column(Integer)
    qdrant_collection: Mapped[str | None] = mapped_column(String(100))
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    agent: Mapped["AIAgent"] = relationship(back_populates="documents")


class AgentConversation(Base, UUIDPKMixin):
    """История диалога ИИ-агента с подписчиком."""

    __tablename__ = "agent_conversations"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Nullable because test-chat from owner (Mini App) has no subscriber attached.
    # Real subscriber conversations from Callback API always set this.
    subscriber_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscribers.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # [{role, content, timestamp}, ...]
    messages: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    credits_spent: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    # 'active', 'closed', 'transferred'
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    agent: Mapped["AIAgent"] = relationship(back_populates="conversations")
    subscriber: Mapped["Subscriber"] = relationship(back_populates="conversations")  # noqa: F821
