from aiogram import Router, F
from misc.utils import config


def setup_routers() -> Router:
    from . import callbacks, admins, admin_handler, user_handler, misc

    user = 0
    router = Router()
    router.message.filter(F.chat.id != config.banned_group)
    if user in config.banned_users:
        router.message.filter(F.user.id != user)

    router.include_router(misc.router)
    router.include_router(admin_handler.router)
    router.include_router(user_handler.router)
    router.include_router(admins.router)
    router.include_router(callbacks.router)

    return router
