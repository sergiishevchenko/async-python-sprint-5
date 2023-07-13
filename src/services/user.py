from abc import ABC, abstractmethod
from typing import Generic, Optional, Type, TypeVar
from uuid import uuid1

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.models import Base
from src.utils.password import get_hashed_password


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)


class Repository(ABC):

    @abstractmethod
    def get_user_by_username(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def create(self, *args, **kwargs):
        raise NotImplementedError


class RepositoryUserDB(Repository, Generic[ModelType, CreateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self._model = model

    async def get_user_by_username(self, db: AsyncSession, obj: CreateSchemaType) -> Optional[ModelType]:
        obj_json = jsonable_encoder(obj)
        statement = select(self._model).where(self._model.username == obj_json['username'])
        results = await db.execute(statement=statement)
        return results.scalar_one_or_none()

    def create_object(self, data: dict):
        extra_obj_data = {}
        user_id = str(uuid1())
        extra_obj_data['id'] = user_id
        password = data.pop('password')
        extra_obj_data['password'] = get_hashed_password(password)
        data.update(extra_obj_data)
        return self._model(**data)

    async def create(self, db: AsyncSession, *, obj: CreateSchemaType) -> ModelType:
        obj_json = jsonable_encoder(obj)
        db_obj = self.create_object(obj_json)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
