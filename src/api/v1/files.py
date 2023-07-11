from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi_cache.backends.redis import RedisCacheBackend
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.core.settings import settings
from src.db.database import get_session
from src.schemes import file, user
from src.services.auth import get_current_user
from src.services.base import file_crud
from src.utils.cache import get_cache, set_cache, get_cache_or_data, redis_cache
from src.utils.files import get_file_data, is_downloadable, get_updated_io_obj_with_media_type


router = APIRouter()


@router.get('/list', response_model=file.FilesList, description='Files list of current user.')
async def get_list(*, db: AsyncSession = Depends(get_session), current_user: user.CurrentUser = Depends(get_current_user),
                   redis_cache: RedisCacheBackend = Depends(redis_cache)) -> Any:
    redis_key = 'list_for_{str()}'.format(current_user.id)
    cache_data = await get_cache(redis_cache, redis_key)
    if not cache_data:
        files = await file_crud.get_list_by_user(db=db, user=current_user)
        files_list = [file.File.from_orm(file).dict() for file in files]
        cache_data = {'current_user_id': current_user.id, 'files': files_list}
        await set_cache(redis_cache, cache_data, redis_key)
    logger.info('List of files of %s', current_user.id)
    return cache_data


@router.post('/upload', response_model=file.FileDB, status_code=status.HTTP_201_CREATED, description='Upload file.')
async def upload_file(*, path: str, db: AsyncSession = Depends(get_session), current_user: user.CurrentUser = Depends(get_current_user),
                      file: UploadFile = File(...)) -> Any:
    if not path.startswith('/'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Path must starts with / .')
    if path.split('/')[-1] == file.filename:
        full_path = path
    else:
        full_path = path + '/' + file.filename
    result = await file_crud.create_or_put_file(db=db, user=current_user, file_obj=file, file_path=full_path)
    logger.info('Upload file %s from %s', full_path, current_user.id)
    return result


@router.get('/download', status_code=status.HTTP_200_OK, description='Download file.')
async def download_file(*, db: AsyncSession = Depends(get_session), current_user: user.CurrentUser = Depends(get_current_user),
                        path: str, compression_type: Optional[str], redis_cache: RedisCacheBackend = Depends(redis_cache)) -> Any:
    if not compression_type:
        redis_key = 'file_info_for_{}'.format(path)
        file_data = await get_cache_or_data(redis_key=redis_key, cache=redis_cache,db_func_obj=get_file_data,
                                            data_schema=file.File, db_func_args=(db, path))
        is_downloadable(file_data=file_data)
        file_url = settings.static_url + file_data.get('path')
        return RedirectResponse(file_url)
    if compression_type not in settings.compression_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Compression type is not supported.')
    updated_io_obj, media_type = await get_updated_io_obj_with_media_type(db=db, redis_cache=redis_cache, path=path, compression_type=compression_type)
    file_name = 'archive' + '.' + compression_type
    logger.info('User %s download file %s', current_user.id, path)
    return StreamingResponse(iter([updated_io_obj.getvalue()]), media_type=media_type, headers={"Content-Disposition": f'attachment;filename={file_name}'})
