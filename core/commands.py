import logging
import os

from aiogram import types, F, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from pydub import AudioSegment

from main import nasty
from misc.ai import OpenAI
from misc.states import DAImage, SDImage, Text, Voice
from misc.utils import config, ClientSD, trim_image
from misc.utils import trim_name, trim_cmd, get_from_dalle

logger = logging.getLogger("__name__")
router = Router()

openai = OpenAI()


@router.message(F.text.startswith("@naastyyaabot"))
async def ask(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.get)
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        trimmed = trim_name(message.text)

        # Generate response
        replay_text = await openai.send_turbo(trimmed)
        try:
            await message.reply(replay_text, parse_mode=None)
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
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        # process the voice message
        file_info = await nasty.get_file(message.voice.file_id)
        file_data = file_info.file_path
        await nasty.download_file(file_data, f"{str(uid)}.ogg")
        sound = AudioSegment.from_file(f"{str(uid)}.ogg", format="ogg")
        sound.export(f"{str(uid)}.wav", format="wav")
        result = openai.send_voice(uid)
        print(result["text"])
        try:
            text_from_ai = result["text"]
            text = openai.send_turbo(text_from_ai)
            await message.reply(f"Голосовое сообщение: {text_from_ai}\n\n{text}", parse_mode=None)
            os.remove(f"{str(uid)}.ogg")
            os.remove(f"{str(uid)}.wav")
        except RuntimeError as err:
            logging.info('error: %s', err)
            text = err
            await message.reply(text, parse_mode=None)


@router.message(Voice.get)
async def process_ask(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Voice.result)
    logging.info("%s", message)


@router.message(Text.get)
async def process_ask21(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.result)
    logging.info("%s", message)


@router.message(F.text.startswith("Нарисуй: "))
async def draw(message: types.Message, state: FSMContext) -> None:
    await state.set_state(DAImage.get)
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        trimmed = trim_cmd(message.text)
        result = openai.send_dalle(trimmed)
        try:
            photo = get_from_dalle(result)
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
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        sd = ClientSD()
        trimmed = trim_image(message.text)
        result = sd.send_sd_img_req(trimmed)
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
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        text = "Бот написан специально для PPRFNK!\n" \
               "По команде /report сообщу всем админам чата о плохом человеке! \n" \
               "Если ошибся или что-то пошло не так напиши /cancel \n" \
               "Хочешь со мной поговорить? Обратись ко мне через никнейм @naastyyaabot ...\n" \
               "Скажи что хочешь нарисовать, я передам это моей подруге нейросети DaLL E, а она нарисует кодовое слово " \
               "'Нарисуй: ...'\n" \
               "Если хочешь отправить картинку моей подруге SD напиши мне 'Представь: ...' --- пока не работает меняю api\n" \
               "\n" \
               "Автор: @vistee"
        await message.reply(text, parse_mode=None)
