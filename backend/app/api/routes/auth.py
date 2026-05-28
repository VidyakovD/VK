from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.db import get_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    validate_vk_launch_params,
)
from app.models import User
from app.schemas import AuthVKRequest, TokenPair, UserRead
from app.services.user_service import get_or_create_user_from_vk

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/vk", response_model=TokenPair)
async def auth_vk(
    body: AuthVKRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenPair:
    """
    Принимает raw launch_params query string от VK Mini App,
    валидирует подпись, создаёт/находит пользователя по vk_user_id, возвращает JWT-пару.
    """
    params = validate_vk_launch_params(body.launch_params)
    if params is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid VK launch_params signature",
        )

    vk_user_id_str = params.get("vk_user_id")
    if not vk_user_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vk_user_id missing in launch_params",
        )
    try:
        vk_user_id = int(vk_user_id_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="vk_user_id is not an integer",
        ) from exc

    user = await get_or_create_user_from_vk(session, vk_id=vk_user_id)

    return TokenPair(
        access_token=create_access_token(subject=str(user.id), extra={"vk_id": vk_user_id}),
        refresh_token=create_refresh_token(subject=str(user.id)),
        expires_in=settings.jwt_access_ttl_seconds,
    )


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
