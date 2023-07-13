from abc import ABC, abstractmethod
from typing import Generic, Optional, Type, TypeVar

from fastapi import File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.models.models import Base
from src.utils.base import get_full_path
from src.utils.directory import create_directory
from src.utils.file import put_file, create_file


ModelType = TypeVar("ModelType", bound=Base)


class Repository(ABC):

    @abstractmethod
    def get_file_by_path(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def get_file_by_id(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def get_list_by_user(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def create_or_put_file(self, *args, **kwargs):
        raise NotImplementedError


class RepositoryFileDB(Repository, Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self._model = model

    async def get_file_by_path(self, db: AsyncSession, file_path: str) -> Optional[ModelType]:
        if not file_path.startswith('/'):
            file_path = '/' + file_path
        statement = select(self._model).where(self._model.path == file_path)
        result = await db.execute(statement=statement)
        return result.scalar_one_or_none()

    async def get_file_by_id(self, db: AsyncSession, file_id: str) -> Optional[ModelType]:
        statement = select(self._model).where(self._model.id == file_id)
        result = await db.execute(statement=statement)
        return result.scalar_one_or_none()

    async def get_list_by_user(self, db: AsyncSession, user: ModelType) -> list[ModelType]:
        statement = select(self._model).where(self._model.user_id == user.id)
        results = await db.execute(statement=statement)
        return results.scalars().all()

    async def create_or_put_file(self, db: AsyncSession, user: ModelType, file: File, file_path: str) -> Optional[ModelType]:
        file_in_storage = await self.get_file_by_path(db=db, file_path=file_path)
        full_path = get_full_path(file_path)
        if file_in_storage:
            return await put_file(db=db, full_path=full_path, file_obj=file_in_storage, file=file)
        else:
            return await create_file(db=db, file_path=file_path, full_path=full_path, create_directory=create_directory,
                                     file=file, model=self._model, user=user)
