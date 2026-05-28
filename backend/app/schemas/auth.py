import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AuthVKRequest(BaseModel):
    """Передаём raw query string из VK Bridge `bridge.send('VKWebAppGetLaunchParams')`."""

    launch_params: str = Field(
        ...,
        description="Raw query string from VK Mini App launch parameters, including sign",
    )


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vk_id: int
    first_name: str | None
    last_name: str | None
    avatar_url: str | None
    credits_balance: Decimal
