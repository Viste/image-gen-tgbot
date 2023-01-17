from aiogram import types, Router, F
from aiogram.filters.command import Command
from misc.utils import config
from misc.language import Lang

router = Router()
router.message.filter(~F.reply_to_message)


@router.message(F.new_chat_members, lambda x: config.remove_joins is True)
async def on_user_join(message: types.Message):
    await message.delete()


@router.message(Command(commands=["report"]))
@router.message(Command(commands=["ro", "nm"]), F.from_user.id.in_(config.admins.keys()))
async def no_reply(message: types.Message, lang: Lang):
    await message.reply(lang.get("error_no_reply"))
