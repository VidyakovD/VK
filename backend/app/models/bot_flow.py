import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class BotFlow(Base, UUIDPKMixin, TimestampMixin):
    """Сценарий чат-бота: JSON-граф нод."""

    __tablename__ = "bot_flows"

    community_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # 'keyword', 'start_command', 'subscribe', 'manual'
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    trigger_value: Mapped[str | None] = mapped_column(Text)
    flow_graph: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    community: Mapped["Community"] = relationship(back_populates="bot_flows")  # noqa: F821
    states: Mapped[list["BotState"]] = relationship(
        back_populates="flow", cascade="all, delete-orphan"
    )


class BotState(Base, UUIDPKMixin):
    """Состояние подписчика в боте. Hot path в Redis с TTL, здесь fallback."""

    __tablename__ = "bot_states"
    __table_args__ = (UniqueConstraint("flow_id", "subscriber_id"),)

    flow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bot_flows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscriber_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscribers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    current_node_id: Mapped[str | None] = mapped_column(String(100))
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    flow: Mapped["BotFlow"] = relationship(back_populates="states")
    subscriber: Mapped["Subscriber"] = relationship(back_populates="bot_states")  # noqa: F821
