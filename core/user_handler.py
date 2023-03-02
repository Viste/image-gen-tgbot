import logging
from typing import List, Union, Optional
from aiogram import types, Bot, html, F, Router
from aiogram.filters.command import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Chat, User, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from misc.utils import DeleteMsgCallback, config, ClientSD, trim_image
from misc.utils import trim_name, trim_cmd, trims, get_from_dalle, get_from_gpt
from misc.states import DAImage, SDImage, Text, Voice
from misc.bridge import OpenAI, Ai21
from misc.language import Lang

logger = logging.getLogger("nasty_bot")
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
    keyboard.button(
        text=lang.get("action_del_msg"),
        callback_data=DeleteMsgCallback(
            action="del",
            entity_id=entity_id,
            message_ids=message_ids
        )
    )
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
                report_chat, text=make_report_message(
                    message.reply_to_message, command.args, lang),
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
            chat, lang.get("need_admins_attention").format(
                msg_url=message.get_url(force_private=True))
        )


@router.message(F.sender_chat, lambda x: config.ban_channels is True)
async def any_message_from_channel(message: types.Message, lang: Lang, bot: Bot):
    if message.is_automatic_forward is None and message.sender_chat.id != message.chat.id:
        await message.answer(lang.get("channels_not_allowed"))
        await bot.ban_chat_sender_chat(message.chat.id, message.sender_chat.id)
        await message.delete()


@router.message(Command(commands=["cancel"]))
@router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    logging.info("%s", message)
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(F.text.startswith("@naastyyaabot"))
async def ask(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.get)
    if message.from_user.id in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        gpt = OpenAI()
        trimmed = trim_name(message.text)
        result = gpt.send_to_gpt(trimmed)
        try:
            text = result["choices"][0]["message"]["content"]
            await message.reply(text, parse_mode=None)
        except ValueError as err:
            logging.info('error: %s', err)
            text = err
            await message.reply(text, parse_mode=None)


@router.message(Text.get)
async def process_ask(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.result)
    logging.info("%s", message)


@router.message(F.content_type.in_({'voice'}))
async def ask(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Voice.get)
    if message.from_user.id in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        gpt = OpenAI()
        voice = message.voice.file_id
        #telegram_voice = await message.voice.get_file()
        # downloaded_file = await bot.download_file(telegram_voice.file_path)
        result = gpt.send_voice(voice)
        try:
            text = result["text"]
            await message.reply(text, parse_mode=None)
        except ValueError as err:
            logging.info('error: %s', err)
            text = err
            await message.reply(text, parse_mode=None)


@router.message(Voice.get)
async def process_ask(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Voice.result)
    logging.info("%s", message)

@router.message(F.text.startswith("Настя,"))
async def ask21(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.get)
    if message.from_user.id in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        ai21 = Ai21()
        trimmed = trims(message.text)
        result = ai21.send_to_ai21(trimmed)
        try:
            print(result)
            text = result['completions'][0]['data']['text']
            await message.reply(text, parse_mode=None)
        except ValueError as err:
            logging.info('error: %s', err)
            text = err
            await message.reply(text, parse_mode=None)


@router.message(Text.get)
async def process_ask21(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.result)
    logging.info("%s", message)


@router.message(F.text.startswith("Нарисуй: "))
async def draw(message: types.Message, state: FSMContext) -> None:
    await state.set_state(DAImage.get)
    if message.from_user.id in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        gpt = OpenAI()
        trimmed = trim_cmd(message.text)
        result = gpt.send_to_dalle(trimmed)
        try:
            photo = get_from_dalle(result['data'])
            await message.reply_photo(photo)
        except ValueError as err:
            logging.info('error: %s', err)
            text = err
            await message.reply(text, parse_mode=None)


@router.message(DAImage.get)
async def process_paint(message: types.Message, state: FSMContext) -> None:
    await state.set_state(DAImage.result)
    logging.info("%s", message)


@router.message(F.text.startswith("Представь: "))
async def imagine(message: types.Message, state: FSMContext) -> None:
    await state.set_state(SDImage.get)
    if message.from_user.id in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        gpt = ClientSD()
        trimmed = trim_image(message.text)
        result = gpt.send_sd_img_req(trimmed)
        try:
            await message.reply_photo(result['output_url'])
        except ValueError as err:
            logging.info('error: %s', err)
            text = err
            await message.reply(text, parse_mode=None)


@router.message(SDImage.get)
async def process_imagine(message: types.Message, state: FSMContext) -> None:
    await state.set_state(SDImage.result)
    logging.info("%s", message)


@router.message(Command(commands="help"))
async def info(message: types.Message):
    if message.from_user.id in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        text = "Бот написан специально для PPRFNK!\n" \
               "По команде /report сообщу всем админам чата о плохом человеке! \n" \
               "Если ошибся или что-то пошло не так напиши /cancel \n" \
               "Хочешь со мной поговорить? Обратись ко мне через никнейм @naastyyaabot ...\n" \
               "Скажи что хочешь нарисовать, я передам это моей подруге нейросети DaLL E, а она нарисует кодовое слово " \
               "'Нарисуй: ...'\n" \
               "Если хочешь отправить картинку моей подруге SD напиши мне 'Представь: ...'\n" \
               "Ai21 -- дич лютая 'Настя, ..\n" \
               "\n" \
               "Автор: @vistee"
        await message.reply(text, parse_mode=None)


# @router.message(F.text.startswith("Настя, как дела?"))
# async def how_are_you(message: types.Message):
#    logging.info("%s", message)
#    gpt = OpenAI()
#    result = await gpt.send_to_gpt(message.text)
#    try:
#        text = result
#        await message.reply(text, parse_mode=None)
#    except ValueError as err:
#        logging.info('error: %s', err)
#        text = err
#        await message.reply(text, parse_mode=None)


async def new_chat_member(message: types.Message):
    pass
