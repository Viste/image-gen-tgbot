import logging
from typing import List, Union, Optional
from aiogram import types, Bot, html, F, Router
from aiogram.filters.command import Command, CommandObject
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Chat, User
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from misc.utils import DeleteMsgCallback
from misc.utils import config
from misc.language import Lang

logger = logging.getLogger("report_bot")
router = Router()

def get_report_chats(bot_id: int) -> List[int]:
    if config.report_mode == "group":
        return [config.group_reports]
    else:
        recipients = []
        for admin_id, permissions in config.admins.items():
            if admin_id != bot_id and permissions.get("can_restrict_members", False) is True:
                recipients.append(admin_id)
        return recipients


def make_report_message(reported_message: types.Message, comment: Optional[str], lang: Lang):
    msg = lang.get("report_message").format(
        time=reported_message.date.strftime(lang.get("report_date_format")),
        msg_url=reported_message.get_url(force_private=True)
    )
    if comment is not None:
        msg += lang.get("report_note").format(note=html.quote(comment))
    return msg


def make_report_keyboard(entity_id: int, message_ids: str, lang: Lang) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    # First button: delete messages only
    keyboard.button(
        text=lang.get("action_del_msg"),
        callback_data=DeleteMsgCallback(
            action="del",
            entity_id=entity_id,
            message_ids=message_ids
        )
    )
    # Second button: delete messages and ban user or channel (user writing on behalf of channel)
    keyboard.button(
        text=lang.get("action_del_and_ban"),
        callback_data=DeleteMsgCallback(
            action="ban",
            entity_id=entity_id,
            message_ids=message_ids
        )
    )
    keyboard.adjust(1)
    return keyboard.as_markup()

@router.message(Command(commands="report"), F.reply_to_message)
async def report(message: types.Message, lang: Lang, bot: Bot, command: CommandObject):
    replied_msg = message.reply_to_message
    reported_chat: Union[Chat, User] = replied_msg.sender_chat or replied_msg.from_user

    if isinstance(reported_chat, User) and reported_chat.id in config.admins.keys():
        await message.reply(lang.get("error_report_admin"))
        return
    else:
        if replied_msg.is_automatic_forward:
            await message.reply(lang.get("error_cannot_report_linked"))
            return
        if reported_chat.id == message.chat.id:
            await message.reply(lang.get("error_report_admin"))
            return

    msg = await message.reply(lang.get("report_sent"))

    for report_chat in get_report_chats(bot.id):
        try:
            await bot.forward_message(
                chat_id=report_chat, from_chat_id=message.chat.id,
                message_id=message.reply_to_message.message_id
            )

            await bot.send_message(
                report_chat, text=make_report_message(message.reply_to_message, command.args, lang),
                reply_markup=make_report_keyboard(
                    entity_id=reported_chat.id,
                    message_ids=f"{message.message_id},{message.reply_to_message.message_id},{msg.message_id}",
                    lang=lang
                )
            )
        except TelegramAPIError as ex:
            logger.error(f"[{type(ex).__name__}]: {str(ex)}")

@router.message(F.text.startswith("@admin"))
async def calling_all_units(message: types.Message, lang: Lang, bot: Bot):
    for chat in get_report_chats(bot.id):
        await bot.send_message(
            chat, lang.get("need_admins_attention").format(msg_url=message.get_url(force_private=True))
        )
@router.message(F.sender_chat, lambda x: config.ban_channels is True)
async def any_message_from_channel(message: types.Message, lang: Lang, bot: Bot):
    # If is_automatic_forward is not None, then this is post from linked channel, which shouldn't be banned
    # If message.sender_chat.id == message.chat.id, then this is an anonymous admin, who shouldn't be banned either
    if message.is_automatic_forward is None and message.sender_chat.id != message.chat.id:
        await message.answer(lang.get("channels_not_allowed"))
        await bot.ban_chat_sender_chat(message.chat.id, message.sender_chat.id)
        await message.delete()