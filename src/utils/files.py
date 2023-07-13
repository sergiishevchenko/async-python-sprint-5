import io
import logging.config
import os.path
import tarfile
import zipfile
from io import BytesIO
from typing import Callable

import py7zr
from fastapi import HTTPException, status
from fastapi_cache.backends.redis import RedisCacheBackend
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.schemes import file as file_schema
from src.services.base import directory_crud, file_crud

from .base import get_full_path
from .cache import get_cache_or_data


async def get_file_data(db: AsyncSession, path: str):
    if path.find('/') != -1:
        file_data = await file_crud.get_file_by_path(db=db, file_path=path)
    else:
        file_data = await file_crud.get_file_by_id(db=db, file_id=path)
    if not file_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='File not found')
    return file_data


def is_file(path: str) -> bool:
    return os.path.isfile(path)


def get_files_paths(full_path: str) -> list:
    result = [os.path.join(full_path, f) for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path, f))]
    return result


async def get_path_by_id(db: AsyncSession, obj_id: str, redis_cache: RedisCacheBackend) -> str:
    redis_key = 'path_for_obj_id_{}'.format(obj_id)
    file_data = await get_cache_or_data(redis_key=redis_key, redis_cache=redis_cache, db_obj=file_crud.get_file_by_id,
                                        data_schema=file_schema.Path, db_args=(db, obj_id), cache_expire=3600)
    if not file_data:
        dir_data = await get_cache_or_data(redis_key=redis_key, redis_cache=redis_cache, db_obj=directory_crud.get_dir_by_id,
                                           data_schema=file_schema.Path, db_args=(db, obj_id), cache_expire=3600)
        if not dir_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return dir_data.get()
    return file_data.get('path')


def compress_file(write_down_to_file: Callable, full_path: str) -> None:
    if is_file(full_path):
        write_down_to_file(full_path)
    else:
        files_paths = get_files_paths(full_path)
        for file_path in files_paths:
            write_down_to_file(file_path)


def zip_files(bytes_io_obj: BytesIO, full_path: str) -> tuple[io.BytesIO, str]:
    with zipfile.ZipFile(bytes_io_obj, mode='w', compression=zipfile.ZIP_DEFLATED) as zip_compressed:
        compress_file(write_down_to_file=zip_compressed.write, full_path=full_path)
        zip_compressed.close()
    return bytes_io_obj, 'application/x-zip-compressed'


def tar_files(bytes_io_obj: BytesIO, full_path: str) -> tuple[io.BytesIO, str]:
    with tarfile.open(fileobj=bytes_io_obj, mode='w:gz') as tar_compressed:
        compress_file(write_down_to_file=tar_compressed.add, full_path=full_path)
        tar_compressed.close()
    return bytes_io_obj, 'application/x-gtar'


def seven_zip_files(bytes_io_obj: BytesIO, full_path: str) -> tuple[io.BytesIO, str]:
    with py7zr.SevenZipFile(bytes_io_obj, mode='w') as seven_zip:
        compress_file(write_down_to_file=seven_zip.write, full_path=full_path)
    return bytes_io_obj, 'application/x-7z-compressed'


COMPRESSION_TYPE = {
    'zip': zip_files,
    'tar': tar_files,
    '7z': seven_zip_files
}


def compress_by_full_path(bytes_io_obj: BytesIO, path: str, compression_type: str):
    full_path = get_full_path(path=path)
    bytes_io_obj, media_type = COMPRESSION_TYPE[compression_type](bytes_io_obj, full_path)
    return bytes_io_obj, media_type


async def get_updated_io_obj_with_media_type(db: AsyncSession, redis_cache: RedisCacheBackend, path: str, compression_type: str) -> tuple[BytesIO, str]:
    bytes_io_obj = BytesIO()
    if path.find('/') == -1:
        path = await get_path_by_id(db=db, obj_id=path, redis_cache=redis_cache)
    if not path.startswith('/'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Path must starts with / .')
    updated_io_obj, media_type = compress_by_full_path(bytes_io_obj=bytes_io_obj, path=path, compression_type=compression_type)
    return updated_io_obj, media_type


def is_downloadable(file_data: dict):
    if not file_data.get('is_downloadable'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You can not download this file.')