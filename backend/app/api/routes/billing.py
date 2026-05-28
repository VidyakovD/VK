from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.db import get_session
from app.models import CreditTransaction, PricingRule, User
from app.schemas import BalanceRead, PricingRuleRead, TransactionRead
from app.services import billing_service

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/balance", response_model=BalanceRead)
async def get_balance(current_user: User = Depends(get_current_user)) -> BalanceRead:
    return BalanceRead(
        credits_balance=current_user.credits_balance,
        trial_ends_at=current_user.trial_ends_at,
    )


@router.get("/transactions", response_model=list[TransactionRead])
async def list_transactions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[TransactionRead]:
    stmt = (
        select(CreditTransaction)
        .where(CreditTransaction.user_id == current_user.id)
        .order_by(CreditTransaction.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    txns = result.scalars().all()
    return [TransactionRead.model_validate(t) for t in txns]


@router.get("/pricing", response_model=list[PricingRuleRead])
async def list_pricing(
    session: AsyncSession = Depends(get_session),
) -> list[PricingRuleRead]:
    """Return current pricing rules, seeding defaults if empty."""
    # Seed all defaults if pricing_rules is empty
    result = await session.execute(select(PricingRule))
    existing = result.scalars().all()
    if not existing:
        for resource_type in billing_service.DEFAULT_PRICING:
            await billing_service.get_rule(session, resource_type)
        result = await session.execute(select(PricingRule))
        existing = result.scalars().all()
    return [PricingRuleRead.model_validate(r) for r in existing]
