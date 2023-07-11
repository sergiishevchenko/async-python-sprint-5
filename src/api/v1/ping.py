from datetime import datetime

import redis.asyncio

from fastapi import APIRouter, status

from src.core.logger import logger
from src.core.settings import settings
from src.db.database import engine
from src.schemes import ping


router = APIRouter()


@router.get('/', response_model=ping.Ping, status_code=status.HTTP_200_OK)
async def send_ping():
    start_time_db = datetime.utcnow()
    async with engine.begin() as conn:
        delta_db = datetime.utcnow()
    total_seconds = (delta_db - start_time_db).total_seconds()
    redis_connection = redis.asyncio.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
    start_time_redis = datetime.utcnow()
    await redis_connection.ping()
    delta_time_redis = datetime.utcnow()
    total_seconds_redis = (delta_time_redis - start_time_redis).total_seconds()
    logger.info('Send ping.')
    return {'db': total_seconds, 'redis': total_seconds_redis}
