import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BalanceRead(BaseModel):
    credits_balance: Decimal
    trial_ends_at: datetime | None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    amount: Decimal
    balance_after: Decimal | None
    description: str | None
    resource_type: str | None
    created_at: datetime


class PricingRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_type: str
    credits_cost: Decimal
    description: str | None
