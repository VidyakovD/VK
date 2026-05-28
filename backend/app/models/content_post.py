import uuid
from datetime import datetime

from sqlalchemy import ARRAY, BigInteger, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPKMixin


class ContentPost(Base, UUIDPKMixin):
    """Пост сообщества — черновик/запланирован/опубликован."""

    __tablename__ = "content_posts"

    community_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str | None] = mapped_column(Text)
    image_urls: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    vk_post_id: Mapped[int | None] = mapped_column(BigInteger)
    # 'draft', 'scheduled', 'published', 'failed'
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    community: Mapped["Community"] = relationship(back_populates="content_posts")  # noqa: F821
