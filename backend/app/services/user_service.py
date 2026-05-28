import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_vk_id(session: AsyncSession, vk_id: int) -> User | None:
    result = await session.execute(select(User).where(User.vk_id == vk_id))
    return result.scalar_one_or_none()


async def get_or_create_user_from_vk(
    session: AsyncSession,
    vk_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    avatar_url: str | None = None,
    trial_days: int = 14,
) -> User:
    """Идемпотентное создание пользователя из VK-данных. Запускает 14-дневный trial при первом входе."""
    user = await get_user_by_vk_id(session, vk_id)
    if user is not None:
        return user

    user = User(
        vk_id=vk_id,
        first_name=first_name,
        last_name=last_name,
        avatar_url=avatar_url,
        trial_ends_at=datetime.now(UTC) + timedelta(days=trial_days),
    )
    session.add(user)
    await session.flush()
    return user
