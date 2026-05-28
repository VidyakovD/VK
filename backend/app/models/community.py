import uuid
from datetime import datetime

from sqlalchemy import ARRAY, BigInteger, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPKMixin


class Community(Base, UUIDPKMixin):
    """Подключённое сообщество ВК."""

    __tablename__ = "communities"
    __table_args__ = (UniqueConstraint("user_id", "vk_group_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vk_group_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    group_name: Mapped[str | None] = mapped_column(String(255))
    group_avatar: Mapped[str | None] = mapped_column(String)

    # Зашифрованный AES-256-GCM access_token сообщества.
    access_token_encrypted: Mapped[str] = mapped_column(String, nullable=False)
    token_permissions: Mapped[list[str] | None] = mapped_column(ARRAY(String))

    callback_server_id: Mapped[int | None] = mapped_column(Integer)
    callback_confirm_code: Mapped[str | None] = mapped_column(String(20))
    callback_secret: Mapped[str | None] = mapped_column(String(64))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="communities")  # noqa: F821
    subscribers: Mapped[list["Subscriber"]] = relationship(  # noqa: F821
        back_populates="community", cascade="all, delete-orphan"
    )
    bot_flows: Mapped[list["BotFlow"]] = relationship(  # noqa: F821
        back_populates="community", cascade="all, delete-orphan"
    )
    mailings: Mapped[list["Mailing"]] = relationship(  # noqa: F821
        back_populates="community", cascade="all, delete-orphan"
    )
    ai_agents: Mapped[list["AIAgent"]] = relationship(  # noqa: F821
        back_populates="community", cascade="all, delete-orphan"
    )
    content_posts: Mapped[list["ContentPost"]] = relationship(  # noqa: F821
        back_populates="community", cascade="all, delete-orphan"
    )
