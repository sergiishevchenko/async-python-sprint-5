from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.db.database import get_session
from src.schemes import user as user_schema
from src.services.base import user_crud


router = APIRouter()


@router.post('/', response_model=user_schema.UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def create_user(*, db: AsyncSession = Depends(get_session), user: user_schema.UserRegister) -> Any:
    user_obj = await user_crud.get_user_by_username(db=db, obj=user)
    if user_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User with this username exists.')
    user = await user_crud.create(db=db, obj=user)
    logger.info('Created user - %s', user.username)
    return user
