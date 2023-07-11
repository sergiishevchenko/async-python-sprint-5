import uvicorn

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi_cache import caches, close_caches
from fastapi_cache.backends.redis import CACHE_KEY, RedisCacheBackend
from fastapi.staticfiles import StaticFiles

from src.api.v1 import base
from src.core.settings import settings


app = FastAPI(title=settings.title, docs_url='/api/openapi', openapi_url='/api/openapi.json',
              default_response_class=ORJSONResponse, swagger_ui_oauth2_redirect_url='/auth/token')

app.include_router(base.router, prefix='/api/v1')
app.mount('/files', StaticFiles(directory=settings.base_dir + '/files'), name='files')


@app.on_event('startup')
async def on_startup() -> None:
    redis_cache = RedisCacheBackend(settings.redis_url)
    caches.set(CACHE_KEY, redis_cache)


@app.on_event('shutdown')
async def on_shutdown() -> None:
    await close_caches()


if __name__ == '__main__':
    uvicorn.run('main:app', host=settings.app_host, port=settings.app_port)
