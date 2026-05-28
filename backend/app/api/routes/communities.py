from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.models import User

router = APIRouter(prefix="/communities", tags=["communities"])


@router.get("")
async def list_communities(current_user: User = Depends(get_current_user)) -> list[dict]:
    """TODO: вернуть подключённые сообщества пользователя."""
    return []
