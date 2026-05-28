import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.db import get_session
from app.core.security import encrypt_token
from app.models import Community, User
from app.schemas import CommunityCreate, CommunityRead
from app.schemas.common import OkResponse

router = APIRouter(prefix="/communities", tags=["communities"])


@router.get("", response_model=list[CommunityRead])
async def list_communities(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[CommunityRead]:
    stmt = (
        select(Community)
        .where(Community.user_id == current_user.id)
        .order_by(Community.connected_at.desc())
    )
    result = await session.execute(stmt)
    communities = result.scalars().all()
    return [CommunityRead.model_validate(c) for c in communities]


@router.post("", response_model=CommunityRead, status_code=status.HTTP_201_CREATED)
async def create_community(
    body: CommunityCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CommunityRead:
    """
    Dev-mode community creation — bypass VK OAuth.
    Stores a placeholder encrypted token; real VK API calls won't work
    until /connect endpoint with real access_token is implemented.
    """
    # Idempotent: return existing if vk_group_id already attached
    existing = await session.execute(
        select(Community).where(
            Community.user_id == current_user.id,
            Community.vk_group_id == body.vk_group_id,
        )
    )
    found = existing.scalar_one_or_none()
    if found is not None:
        return CommunityRead.model_validate(found)

    community = Community(
        user_id=current_user.id,
        vk_group_id=body.vk_group_id,
        group_name=body.group_name,
        group_avatar=body.group_avatar,
        access_token_encrypted=encrypt_token("DEV_PLACEHOLDER_TOKEN"),
        is_active=True,
    )
    session.add(community)
    await session.flush()
    return CommunityRead.model_validate(community)


@router.delete("/{community_id}", response_model=OkResponse)
async def delete_community(
    community_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OkResponse:
    community = await session.get(Community, community_id)
    if community is None or community.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Community not found")
    await session.delete(community)
    return OkResponse()
