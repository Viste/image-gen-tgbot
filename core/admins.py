from aiogram import types, Router
from filters.admins import AdminAdded, AdminRemoved
from misc.utils import config

router = Router()


@router.chat_member(AdminAdded())
async def admin_added(event: types.ChatMemberUpdated):
    new = event.new_chat_member
    if new.status == "creator":
        config.admins[new.user.id] = {"can_restrict_members": True}
    else:
        config.admins[new.user.id] = {"can_restrict_members": new.can_restrict_members}


@router.chat_member(AdminRemoved())
async def admin_removed(event: types.ChatMemberUpdated):
    new = event.new_chat_member
    if new.user.id in config.keys():
        del config.admins[new.user.id]
