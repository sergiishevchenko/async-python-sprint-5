import os.path
from datetime import datetime
from typing import Callable, Type

from aioshutil import copyfileobj
from fastapi import File
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import File as FileModel, User
from src.core.settings import settings


async def write_down_to_file(file: File, full_path: str):
    with open(full_path, 'wb') as f:
        await copyfileobj(file.file, f)


async def create_file(db: AsyncSession, file_path: str, full_path: str, create_directory: Callable, file: File,
                      model: Type[FileModel], user: Type[User]):
    files_path = settings.files_path
    for dir_name in file_path.split('/')[1:-1]:
        path = os.path.join(files_path, dir_name)
        if os.path.exists(path):
            continue
        else:
            os.mkdir(path)
            await create_directory(db=db, path=path)
    await write_down_to_file(file=file, full_path=full_path)
    size = os.path.getsize(full_path)
    created_file = model(name=file.filename, path=file_path, size=size, is_downloadable=True, user=user)

    db.add(created_file)
    await db.commit()
    await db.refresh(created_file)
    return created_file


async def put_file(db: AsyncSession, file: File, full_path: str, file_obj: Type[FileModel]):
    await write_down_to_file(file=file, full_path=full_path)
    size = os.path.getsize(full_path)
    file_obj.size = size
    file_obj.created_at = datetime.utcnow()

    await db.commit()
    await db.refresh(file_obj)
    return file_obj
