import html
import logging
import random
import os
import base64
import uuid

from aiogram import types, F, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import BufferedInputFile
from fluent.runtime import FluentLocalization
from pydub import AudioSegment

from main import nasty
from core.helpers.tools import send_reply, reply_if_banned, handle_exception
from core.helpers.ai.MJWorker import Midjourney
from core.helpers.ai.conversation import OpenAI
from core.helpers.ai.stadif import StableDiffAI
from core.helpers.ai.sdapi import SDAI
from core.helpers.ai.voice import ELAI
from tools.states import DAImage, SDImage, Text, MJImage, Voice
from tools.utils import load_params, split_into_chunks

logger = logging.getLogger(__name__)

router = Router()
openai = OpenAI()
elevenlabs = ELAI()
stable_diff_ai = StableDiffAI()
sd_ai = SDAI()
params = load_params("params.json")
params_file = "params.json"


@router.message(F.text.startswith("@naastyyaabot"))
async def start_chat(message: types.Message, state: FSMContext,  l10n: FluentLocalization) -> None:
    uid = message.from_user.id
    if await reply_if_banned(message, uid, l10n):
        return
    else:
        logger.info("Message: %s", message)

        text = html.escape(message.text)
        escaped_text = text.strip('@naastyyaabot ')

        await state.set_state(Text.get)
        replay_text, total_tokens = await openai.get_resp(escaped_text, uid)
        chunks = split_into_chunks(replay_text)
        for index, chunk in enumerate(chunks):
            if index == 0:
                await send_reply(message, chunk)


@router.message(Text.get, F.reply_to_message.from_user.is_bot)
async def process_chat(message: types.Message, l10n: FluentLocalization) -> None:
    uid = message.from_user.id
    if await reply_if_banned(message, uid, l10n):
        return

    text = html.escape(message.text)

    replay_text, total_tokens = await openai.get_resp(text, uid)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        if index == 0:
            await send_reply(message, chunk)


@router.message(F.text.startswith("Нарисуй: "))
async def paint(message: types.Message, state: FSMContext, l10n: FluentLocalization) -> None:
    uid = message.from_user.id
    if await reply_if_banned(message, uid, l10n):
        return
    else:
        logger.info("Message: %s", message)
        await state.set_state(DAImage.get)

        text = html.escape(message.text)
        escaped_text = text.strip('Нарисуй: ')
        result = await openai.send_dalle(escaped_text)

        logger.info("Response from DaLLe: %s", result)
        try:
            photo = result
            await message.reply_photo(types.URLInputFile(photo))
        except Exception as err:
            await handle_exception(message, err, logger)


@router.message(DAImage.get)
async def process_paint(message: types.Message, state: FSMContext) -> None:
    await state.set_state(DAImage.result)
    logger.info("%s", message)


@router.message(F.text.startswith("Отобрази: "))
async def draw(message: types.Message, state: FSMContext, l10n: FluentLocalization) -> None:
    uid = message.from_user.id
    if await reply_if_banned(message, uid, l10n):
        return
    else:
        logger.info("Message: %s", message)
        await state.set_state(MJImage.get)
        image_generators = [Midjourney(params_file, i) for i in range(10)]

        text = html.escape(message.text)
        escaped_text = text.strip('Отобрази: ')
        image_generator = random.choice(image_generators)
        resp = await image_generator.get_images(escaped_text)

        logger.info("Response From IMG-GENERATOR: %s", resp)
        try:
            photo = resp[0]['url']
            uid = resp[0]['uuid']
            message_id = resp[0]['id']

            await state.update_data(msg_id=message_id)
            await state.update_data(image_generator=image_generators.index(image_generator))
            await state.update_data(uuid=uid)

            logger.info("Result Photo Url: %s", photo)
            logger.info("Result PhotoUUID: %s", uid)
            logger.info("Result MessageID: %s", message_id)
            logger.info("Result ChannelID: %s", image_generators.index(image_generator))

            builder = InlineKeyboardBuilder()
            for i in range(1, 5):
                logger.info("Image Generator Index: %s", image_generators.index(image_generator))
                builder.add(types.InlineKeyboardButton(text=f"Upscale {i}", callback_data=f"ups:{i}"))
            builder.adjust(4)
            await message.reply_photo(photo=types.URLInputFile(photo), caption="какое изображение будет увеличивать?", reply_markup=builder.as_markup(resize_keyboard=True))
        except Exception as err:
            await handle_exception(message, err, logger)


@router.message(MJImage.get)
async def process_draw(message: types.Message, state: FSMContext) -> None:
    await state.set_state(MJImage.result)
    logger.info("%s", message)


@router.message(F.text.startswith("Представь: "))
async def imagine(message: types.Message, state: FSMContext, l10n: FluentLocalization) -> None:
    uid = message.from_user.id
    if await reply_if_banned(message, uid, l10n):
        return
    else:
        logger.info("Message: %s", message)
        await state.set_state(SDImage.get)

        text = html.escape(message.text)
        escaped_text = text.strip('Представь: ')
        result = await sd_ai.s2sdapi(escaped_text)

        logger.info("Result: %s", result)
        try:
            base64_image = result
            image_bytes = base64.b64decode(base64_image)
            filename = f"{uuid.uuid4()}.jpg"

            await message.reply_photo(photo=BufferedInputFile(image_bytes, filename=filename))
        except Exception as err:
            await handle_exception(message, err, logger)


@router.message(SDImage.get)
async def process_imagine(message: types.Message, state: FSMContext) -> None:
    await state.set_state(SDImage.result)
    logger.info("Message: %s", message)


@router.message(F.content_type.in_({'voice'}))
async def voice_dialogue(message: types.Message, state: FSMContext, l10n: FluentLocalization) -> None:
    uid = message.from_user.id
    if await reply_if_banned(message, uid, l10n):
        return
    else:
        await state.set_state(Voice.get)

        file_info = await nasty.get_file(message.voice.file_id)
        file_data = file_info.file_path

        await nasty.download_file(file_data, f"{str(uid)}.ogg")

        sound = AudioSegment.from_file(f"{str(uid)}.ogg", format="ogg")
        sound.export(f"{str(uid)}.wav", format="wav")
        result = await openai.send_voice(uid)

        try:
            logger.info("RESULT voice from OAI: %s", result.text)
            text_from_ai = result.text
            text, tokens = await openai.get_resp(text_from_ai, uid)
            voice_filename = elevenlabs.send2api(str(text), uid)

            logger.info("TexT sent to 11labs: %s", text)
            logger.info("voice filename: %s", voice_filename)

            with open(voice_filename, 'rb') as f:
                voice_bytes = f.read()

            filename = f"{uuid.uuid4()}.mp3"
            await message.reply_voice(BufferedInputFile(voice_bytes, filename=filename))

            os.remove(f"{str(uid)}.ogg")
            os.remove(f"{str(uid)}.wav")
            os.remove(voice_filename)

        except RuntimeError as err:
            logging.info('error: %s', err)
            text = "error in audio process"
            await message.reply(text, parse_mode=None)


@router.message(Voice.get)
async def process_show(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Voice.result)
    logger.info("Message: %s", message)


@router.message(Command(commands="help"))
async def info_user(message: types.Message, l10n: FluentLocalization):
    await message.answer(l10n.format_value("help"))
