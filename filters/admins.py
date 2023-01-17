from aiogram.types import ChatMemberUpdated
from aiogram.filters import BaseFilter


class AdminAdded(BaseFilter):
    async def __call__(self, event: ChatMemberUpdated) -> bool:
        return event.new_chat_member.status in ("creator", "administrator")


class AdminRemoved(BaseFilter):
    async def __call__(self, event: ChatMemberUpdated) -> bool:
        return event.old_chat_member.status in ("creator", "administrator") \
            and event.new_chat_member.status not in ("creator", "administrator")
