import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPKMixin


class CreditTransaction(Base, UUIDPKMixin):
    """Транзакция по кредитам: пополнение / списание / возврат / бонус."""

    __tablename__ = "credit_transactions"
    __table_args__ = (Index("ix_credit_tx_user_date", "user_id", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 'topup', 'spend', 'refund', 'bonus'
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    balance_after: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    description: Mapped[str | None] = mapped_column(Text)
    # 'message', 'llm_request', 'image_gen', 'topup_yookassa', etc.
    resource_type: Mapped[str | None] = mapped_column(String(50))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="credit_transactions")  # noqa: F821


class PricingRule(Base, UUIDPKMixin):
    """Тарифный коэффициент за ресурс — управляется админом."""

    __tablename__ = "pricing_rules"

    # 'message_send', 'openai_gpt4o_1k_tokens', 'image_gpt_image_2', etc.
    resource_type: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    credits_cost: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
