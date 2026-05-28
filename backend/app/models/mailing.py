import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPKMixin


class Mailing(Base, UUIDPKMixin):
    """Рассылка: текст + сегмент + расписание + счётчики."""

    __tablename__ = "mailings"
    __table_args__ = (Index("ix_mailings_status_scheduled", "status", "scheduled_at"),)

    community_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    message_text: Mapped[str | None] = mapped_column(Text)
    attachments: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    segment_filter: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # 'draft', 'scheduled', 'sending', 'completed', 'failed'
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")

    total_recipients: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    community: Mapped["Community"] = relationship(back_populates="mailings")  # noqa: F821
