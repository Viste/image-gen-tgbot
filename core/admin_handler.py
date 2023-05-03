import re
from datetime import timedelta

from aiogram import types, Bot, Router, F
from aiogram.filters.command import Command

from tools.ai_tools import OpenAI
from tools.language import Lang
from tools.utils import config

restriction_time_regex = re.compile(r'(\b[1-9][0-9]*)([mhd]\b)')
router = Router()
openai = OpenAI()


def get_restriction_period(text: str) -> int:
    multipliers = {"m": 60, "h": 3600, "d": 86400}
    if match := re.search(restriction_time_regex, text):
        time, modifier = match.groups()
        return int(time) * multipliers[modifier]
    return 0


@router.message(Command(commands=["ro", "nm"]), F.reply_to_message, F.from_user.id.in_(config.admins))
async def cmd_ro_or_nomedia(message: types.Message, lang: Lang, bot: Bot):
    if message.reply_to_message.from_user.id in config.admins.keys():
        await message.reply(lang.get("error_restrict_admin"))
        return
    if config.admins.get(message.from_user.id, {}).get("can_restrict_members", False) is False:
        await message.reply(lang.get("error_cannot_restrict"))
        return

    # If a message is sent on behalf of channel, then we can only ban it
    if message.reply_to_message.sender_chat is not None and message.reply_to_message.is_automatic_forward is None:
        await bot.ban_chat_sender_chat(message.chat.id, message.reply_to_message.sender_chat.id)
        await message.reply(lang.get("channel_banned_forever"))
        return

    restriction_period = get_restriction_period(message.text)
    restriction_end_date = message.date + timedelta(seconds=restriction_period)

    is_ro = message.text.startswith("/ro")
    str_forever = "readonly_forever" if is_ro else "nomedia_forever"
    str_temporary = "readonly_temporary" if is_ro else "nomedia_temporary"
    permissions = types.ChatPermissions() if is_ro else types.ChatPermissions(can_send_messages=True)

    await bot.restrict_chat_member(
        chat_id=message.chat.id,
        user_id=message.reply_to_message.from_user.id,
        permissions=permissions,
        until_date=restriction_end_date
    )

    if restriction_period == 0:
        await message.reply(lang.get(str_forever))
    else:
        await message.reply(lang.get(str_temporary).format(
            time=restriction_end_date.strftime("%d.%m.%Y %H:%M")
        ))


@router.message(F.from_user.id.in_(config.admins), Command(commands="money"))
async def usage(message: types.Message):
    text = openai.get_money()
    await message.reply(text, parse_mode=None)
