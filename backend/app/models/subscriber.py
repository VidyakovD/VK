import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import ARRAY, BigInteger, Boolean, Date, DateTime, ForeignKey, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPKMixin


class Subscriber(Base, UUIDPKMixin):
    """Подписчик сообщества — для сегментации, хранения переменных, статуса 24ч окна."""

    __tablename__ = "subscribers"
    __table_args__ = (UniqueConstraint("community_id", "vk_user_id"),)

    community_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vk_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    sex: Mapped[int | None] = mapped_column(SmallInteger)  # 1=female, 2=male
    city: Mapped[str | None] = mapped_column(String(100))
    birth_date: Mapped[date | None] = mapped_column(Date)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    variables: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    last_interaction_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    can_message: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    community: Mapped["Community"] = relationship(back_populates="subscribers")  # noqa: F821
    bot_states: Mapped[list["BotState"]] = relationship(  # noqa: F821
        back_populates="subscriber", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["AgentConversation"]] = relationship(  # noqa: F821
        back_populates="subscriber", cascade="all, delete-orphan"
    )
