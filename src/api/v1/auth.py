from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.db.database import get_session
from src.schemes import user
from src.services.auth import get_token


router = APIRouter()


@router.post('/token', response_model=user.TokenUI)
async def get_access_token(*, db: AsyncSession = Depends(get_session), form: OAuth2PasswordRequestForm = Depends()):
    access_token = await get_token(db=db, username=form.username, password=form.password)
    logger.info('Send token for %s', form.username)
    return access_token


@router.post('/auth', response_model=user.Token)
async def get_token_for_user(*, db: AsyncSession = Depends(get_session), obj: user.UserAuth):
    username, password = obj.username, obj.password
    access_token = await get_token(db=db, username=username, password=password)
    logger.info('Send token for %s', username)
    return access_token
