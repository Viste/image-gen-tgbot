import logging
import random

from aiogram import types, Bot, Router
from aiogram.exceptions import TelegramAPIError

from artint.MJWorker import Midjourney
from tools.language import Lang
from tools.utils import DeleteMsgCallback
from tools.utils import config, load_params

logger = logging.getLogger("nasty_bot")
router = Router()

params = load_params("params.json")
params_file = "params.json"

# Create a list of ImageGenerator instances for each channel
image_generators = [Midjourney(params_file, i) for i in range(10)]


@router.callback_query(DeleteMsgCallback.filter())
async def delmsg_callback(call: types.CallbackQuery, callback_data: DeleteMsgCallback,
                          lang: Lang, bot: Bot):
    delete_ok: bool = True
    for msg_id in callback_data.message_ids.split(","):
        try:
            await bot.delete_message(config.group_main, int(msg_id))
        except TelegramAPIError as ex:
            # Todo: better pointer at message which caused this error
            logger.error(f"[{type(ex).__name__}]: {str(ex)}")
            delete_ok = False

    if callback_data.action == "del":
        await call.message.edit_text(call.message.html_text + lang.get("action_deleted"))
    elif callback_data.action == "ban":
        try:
            # if a channel was reported
            if callback_data.entity_id < 0:
                await bot.ban_chat_sender_chat(config.group_main, callback_data.entity_id)
            # if a user was reported
            else:
                await bot.ban_chat_member(config.group_main, callback_data.entity_id)
            await call.message.edit_text(call.message.html_text + lang.get("action_deleted_banned"))
        except TelegramAPIError as ex:
            logger.error(f"[{type(ex).__name__}]: {str(ex)}")
            delete_ok = False

    if delete_ok:
        await call.answer()
    else:
        await call.answer(show_alert=True, text=lang.get("action_deleted_partially"))


@router.callback_query(lambda c: c.data and c.data.startswith('upscale:'))
async def process_callback(call: types.CallbackQuery):
    _, message_id, number, uuid = call.data.split(":")
    image_generator = random.choice(image_generators)
    try:
        result = await image_generator.send_upscale_request(message_id, number, uuid)
        await call.message.answer(result)
        await call.answer()
    except Exception as e:
        await call.answer(show_alert=True, text=f"{e}")
