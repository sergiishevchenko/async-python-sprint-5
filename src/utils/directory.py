import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import Directory


async def create_directory(db: AsyncSession, path: str) -> Directory:
    directory_id = str(uuid.uuid1())
    directory_obj = Directory(id=directory_id, path=path)

    db.add(directory_obj)
    await db.commit()
    await db.refresh(directory_obj)
    return directory_obj
