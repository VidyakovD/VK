import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models import CreditTransaction, PricingRule, User

log = get_logger(__name__)


# Default tariffs (credits per unit). Seeded into pricing_rules on first use.
DEFAULT_PRICING: dict[str, tuple[Decimal, str]] = {
    "message_send":              (Decimal("0.10"), "Отправка сообщения подписчику"),
    "openai_gpt4o_1k_tokens":    (Decimal("5.00"), "GPT-4o 1K токенов (in+out)"),
    "anthropic_claude_1k_tokens":(Decimal("6.00"), "Claude Sonnet 1K токенов"),
    "openai_embedding_1k_tokens":(Decimal("0.02"), "text-embedding-3-small 1K токенов"),
    "openai_image_gpt2":         (Decimal("8.00"), "gpt-image-2 (одна картинка high)"),
    "kb_indexing_per_1mb":       (Decimal("5.00"), "Индексация документа БЗ (1 MB)"),
    "autopost":                  (Decimal("0.50"), "Автопостинг (1 пост)"),
}


async def get_rule(session: AsyncSession, resource_type: str) -> PricingRule:
    """Get pricing rule, seeding from defaults on first lookup."""
    result = await session.execute(
        select(PricingRule).where(PricingRule.resource_type == resource_type)
    )
    rule = result.scalar_one_or_none()
    if rule is not None:
        return rule

    if resource_type not in DEFAULT_PRICING:
        raise ValueError(f"Unknown resource_type '{resource_type}' and no default")
    cost, desc = DEFAULT_PRICING[resource_type]
    rule = PricingRule(resource_type=resource_type, credits_cost=cost, description=desc)
    session.add(rule)
    await session.flush()
    log.info("billing.rule.seeded", resource_type=resource_type, cost=str(cost))
    return rule


async def cost_for_llm_call(
    session: AsyncSession,
    provider: str,
    tokens_in: int,
    tokens_out: int,
) -> Decimal:
    total_k = Decimal(tokens_in + tokens_out) / Decimal(1000)
    if provider == "anthropic":
        rule = await get_rule(session, "anthropic_claude_1k_tokens")
    else:
        rule = await get_rule(session, "openai_gpt4o_1k_tokens")
    return (rule.credits_cost * total_k).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


async def cost_for_embedding(session: AsyncSession, tokens: int) -> Decimal:
    rule = await get_rule(session, "openai_embedding_1k_tokens")
    return (rule.credits_cost * Decimal(tokens) / Decimal(1000)).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )


class InsufficientCredits(Exception):
    pass


async def debit_credits(
    session: AsyncSession,
    user: User,
    amount: Decimal,
    resource_type: str,
    description: str | None = None,
    resource_id: uuid.UUID | None = None,
) -> CreditTransaction:
    """Debit credits from user balance. Raises InsufficientCredits if balance would go negative."""
    if amount <= 0:
        raise ValueError("Debit amount must be positive")
    if user.credits_balance < amount:
        raise InsufficientCredits(
            f"Balance {user.credits_balance} < required {amount}"
        )
    user.credits_balance = (user.credits_balance - amount).quantize(Decimal("0.01"))
    txn = CreditTransaction(
        user_id=user.id,
        type="spend",
        amount=-amount,
        balance_after=user.credits_balance,
        description=description,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    session.add(txn)
    await session.flush()
    log.info(
        "billing.debit",
        user=str(user.id),
        amount=str(amount),
        resource_type=resource_type,
        balance_after=str(user.credits_balance),
    )
    return txn


async def credit_topup(
    session: AsyncSession,
    user: User,
    amount: Decimal,
    resource_type: str = "topup_yookassa",
    description: str | None = None,
) -> CreditTransaction:
    if amount <= 0:
        raise ValueError("Topup amount must be positive")
    user.credits_balance = (user.credits_balance + amount).quantize(Decimal("0.01"))
    txn = CreditTransaction(
        user_id=user.id,
        type="topup",
        amount=amount,
        balance_after=user.credits_balance,
        description=description,
        resource_type=resource_type,
    )
    session.add(txn)
    await session.flush()
    return txn
