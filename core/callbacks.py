import logging

from aiogram import types, Bot, Router, F
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from core.helpers.ai import Midjourney
from tools.language import Lang
from tools.utils import DeleteMsgCallback
from tools.utils import config, load_params

logger = logging.getLogger(__name__)
router = Router()
params = load_params("params.json")
params_file = "params.json"


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


@router.callback_query(F.data.startswith('ups:'))
async def upscase_callback(callback: types.CallbackQuery, state: FSMContext):
    _, number = callback.data.split(":")
    data = await state.get_data()
    img_gen = data['image_generator']
    message_id = data['msg_id']
    uuid = data['uuid']
    image_generators = Midjourney(params_file, img_gen)
    try:
        result = await image_generators.upscale(message_id, number, uuid)
        logger.info("Callback result: %s", result)
        await callback.message.reply_photo(result, reply_markup=ReplyKeyboardRemove())
        await callback.answer()
    except Exception as e:
        await callback.answer(show_alert=True, text=f"{e}")
