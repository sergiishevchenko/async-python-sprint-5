from fastapi import APIRouter

from . import auth, files, ping, register


router = APIRouter()


router.include_router(auth.router, prefix='/auth', tags=['auth'])

router.include_router(register.router, prefix='/register', tags=['register'])

router.include_router(files.router, prefix='/files', tags=['files'])

router.include_router(ping.router, prefix='/ping', tags=['ping'])