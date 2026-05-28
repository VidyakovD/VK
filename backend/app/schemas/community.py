import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommunityCreate(BaseModel):
    """Dev-mode community creation. Production flow uses VK OAuth callback
    and posts to /connect with an encrypted access_token."""

    vk_group_id: int = Field(..., gt=0)
    group_name: str = Field(min_length=1, max_length=255)
    group_avatar: str | None = None


class CommunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vk_group_id: int
    group_name: str | None
    group_avatar: str | None
    is_active: bool
    connected_at: datetime
