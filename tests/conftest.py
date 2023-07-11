import asyncio
import os
import shutil
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi_cache import caches
from fastapi_cache.backends.redis import RedisCacheBackend
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.settings import settings
from src.main import app
from src.models.models import Base, get_session
from src.utils.cache import redis_cache


def get_test_engine():
    return create_async_engine(os.getenv('TEST_DATABASE_URL'), echo=True, future=True)


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def engine():
    engine = get_test_engine()
    yield engine
    engine.sync_engine.dispose()


@pytest.fixture(scope="session")
def async_session(engine):
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def create_base(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session")
async def test_app(engine, create_base):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def get_test_session() -> AsyncSession:
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    redis_cache = RedisCacheBackend(settings.redis_url_local)
    caches.set('TEST_REDIS', redis_cache)

    def redis_test_cache():
        return caches.get('TEST_REDIS')

    app.dependency_overrides[redis_cache] = redis_test_cache
    yield app


@pytest_asyncio.fixture(scope="session")
async def auth_client(test_app):
    test_user = 'test_user_1'
    test_password = test_user
    async with AsyncClient(app=test_app, base_url='http://127.0.0.1:8080/api/v1') as client:
        await client.post(
            '/register/',
            json={
                'username': test_user,
                'password': test_password
            }
        )
        response_success = await client.post(
            '/auth/',
            json={
                'username': test_user,
                'password': test_password
            }
        )
        token = 'Bearer ' + response_success.json()['access_token']
        client.headers = {'Authorization': token}
        yield client


@pytest_asyncio.fixture(scope="session")
async def auth_client_with_file(auth_client):
    file_path = Path('test_file.txt')
    file = {'file': file_path.open('rb')}
    await auth_client.post(
        '/files/upload',
        params={
            'path': '/test'
        },
        files=file,
    )
    yield auth_client
    shutil.rmtree(settings.files_path + '/test')
