from aiogram import Router, F

from tools.utils import config


def setup_routers() -> Router:
    from . import callbacks, admins, admin_handler, users, commands, misc
    from core.helpers import callbacks, payment

    router = Router()
    router.message.filter(F.chat.id != config.banned_group)

    router.include_router(admins.router)
    router.include_router(admin_handler.router)
    router.include_router(users.router)
    router.include_router(commands.router)
    router.include_router(misc.router)
    router.include_router(callbacks.router)

    return router
