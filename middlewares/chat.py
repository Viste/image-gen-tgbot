import asyncio
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import CallbackQuery
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import gettext as _

from misc.utils import DeleteMsgCallback


class ActionMiddleware(BaseMiddleware):

    def __init__(self, config) -> None:

        self.config = config

    async def __call__(
            self,
            handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
            event: CallbackQuery,
            data: dict[str, Any]
    ) -> Any:

        data['config'] = self.config
        action = get_flag(data, "chat_action")
        if not action:
            return await handler(event, data)
        async with ChatActionSender(action=action, chat_id=event.message.chat.id):
            handler_cor = handler(event, data)
            try:
                return await asyncio.wait_for(handler_cor, timeout=15)
            except asyncio.TimeoutError:
                DeleteMsgCallback(action="del", message_ids=event.message.message_id)
                return await event.message.answer(_("⚠ Превышено время ожидания ответа :(\n 🔄 Попробуйте снова❕"))
