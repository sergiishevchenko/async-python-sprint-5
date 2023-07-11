from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, validator


class ORM(BaseModel):

    class Config:
        orm_mode = True


class FilesList(ORM):
    account_id: UUID
    files: List


class Path(ORM):
    path: str


class FileBase(ORM):
    id: UUID
    name: str
    path: str
    size: int
    is_downloadable: bool
    created_at: datetime


class FileDB(FileBase):

    @validator('created_at')
    def time_to_str(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        else:
            return value


class File(FileBase):

    @validator('created_at', pre=True)
    def time_to_str(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        else:
            return value
