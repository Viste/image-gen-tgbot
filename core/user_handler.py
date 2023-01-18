import logging
from typing import List, Union, Optional
from aiogram import types, Bot, html, F, Router
from aiogram.filters.command import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import Chat, User, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup
from misc.utils import DeleteMsgCallback, config, result_to_text, ClientChatGPT, result_to_url, trim_name
from misc.language import Lang

logger = logging.getLogger("nasty_bot")
router = Router()


class Text(StatesGroup):
    get = State()
    res = State()


class DaleImage(StatesGroup):
    get = State()
    res = State()


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
    # If is_automatic_forward is not None, then this is post from linked channel, which shouldn't be banned
    # If message.sender_chat.id == message.chat.id, then this is an anonymous admin, who shouldn't be banned either
    if message.is_automatic_forward is None and message.sender_chat.id != message.chat.id:
        await message.answer(lang.get("channels_not_allowed"))
        await bot.ban_chat_sender_chat(message.chat.id, message.sender_chat.id)
        await message.delete()


@router.message(Command(commands=["cancel"]))
@router.message(F.text.casefold() == "cancel")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info("Cancelling state %r", current_state)
    await state.clear()
    await message.answer(
        "Cancelled.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(F.text.startswith("@naastyyaabot"))
async def ask(message: types.Message, lang: Lang, state: FSMContext) -> None:
    await state.set_state(Text.get)
    gpt = ClientChatGPT()
    trimmed = trim_name(message.text)
    result = await gpt.send_qa_to_gpt(trimmed)
    try:
        text = result_to_text(result["choices"])
        await message.reply(text)
    except(TimeoutError, KeyError, TelegramBadRequest) as e:
        logging.info('error: %s', e)
        if e == TimeoutError:
            text = lang.get("error_timeout")
            await message.reply(text)
        elif e == KeyError:
            text = lang.get("error_key")
            await message.reply(text)
        elif e == TelegramBadRequest:
            text = lang.get("error_bad")
            await message.reply(text)


@router.message(Text.get)
async def process_ask(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.res)
    logging.info("%s", message.text)


@router.message(Command(commands="paint"))
async def ask(message: types.Message, state: FSMContext) -> None:
    await state.set_state(DaleImage.get)
    text_message = "Опиши что ты хочешь увидеть на изображении?"
    await message.reply(text_message)


@router.message(DaleImage.get)
async def process_paint(message: types.Message, lang: Lang, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(DaleImage.res)
    logging.info("%s", message.text)
    gpt = ClientChatGPT()
    result = await gpt.send_dale_img_req(message.text)
    try:
        photo = result_to_url(result["data"])
        await message.reply_photo(photo)
    except(TimeoutError, KeyError, TelegramBadRequest) as e:
        logging.info('error: %s', e)
        if e == TimeoutError:
            text = lang.get("error_timeout")
            await message.reply(text)
        elif e == KeyError:
            text = lang.get("error_key")
            await message.reply(text)
        elif e == TelegramBadRequest:
            text = lang.get("error_bad")
            await message.reply(text)


@router.message(Command(commands="help"))
async def info(message: types.Message):
    text = "Бот написан специально для PPRFNK!\n" \
           "По команде /report сообщу всем админам чата о плохом человеке! \n" \
           "Если ошибся или что-то пошло не так напиши /cancel \n" \
           "По команде /ask я дам один ответ на один вопрос\n" \
           "По команде /paint сгенерирую изображение с помощью моей подруги нейросети DaLL E\n" \
           "Еще скоро появится команда /dream для генерации изображений в нейросети SD, но пока мой автор ленится\n" \
           "\n" \
           "Автор: @vistee"
    await message.reply(text)


@router.message(F.text.startswith("Настя, как дела?"))
async def how_are_you(message: types.Message, lang: Lang):
    logging.info("%s", message.text)
    gpt = ClientChatGPT()
    result = await gpt.send_qa_to_gpt(message.text)
    try:
        text = result_to_text(result["choices"])
        await message.reply(text)
    except(TimeoutError, KeyError) as e:
        logging.info('error: %s', e)
        if e == TimeoutError:
            text = (lang.get("error_timeout"))
            await message.reply(text)
        elif e == KeyError:
            text = (lang.get("error_key"))
            await message.reply(text)
        elif e == TelegramBadRequest:
            text = (lang.get("error_bad"))
            await message.reply(text)


async def new_chat_member(message: types.Message):
    pass
