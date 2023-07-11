from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.settings import settings
from src.db.database import get_session
from src.models.models import User
from src.schemes import user as user_schema
from src.utils.password import verify_password


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='v1/auth/token')


async def get_user(db: AsyncSession, username: str):
    statement = select(User).where(User.username == username)
    results = await db.execute(statement=statement)
    return results.scalar_one_or_none()


async def auth_user(db: AsyncSession, username: str, password: str):
    user = await get_user(db=db, username=username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


async def get_current_user(db: AsyncSession = Depends(get_session), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = user_schema.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(db=db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def create_access_token(data: dict, delta: Union[timedelta, None] = None):
    data_to_encode = data.copy()
    if delta:
        expire = datetime.utcnow() + delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    data_to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(data_to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


async def get_token(db: AsyncSession, username: str, password: str):
    user: Union[User, bool] = await auth_user(db, username, password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=settings.token_expire)
    token = create_access_token(data={'sub': user.username}, delta=access_token_expires)
    return {'access_token': token, 'token_type': 'bearer'}
