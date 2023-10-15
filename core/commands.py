import html
import logging
import random
import asyncio
import io
import base64
import tempfile
from aiogram import types, F, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluent.runtime import FluentLocalization
from PIL import Image

from tools.ai.MJWorker import Midjourney
from tools.ai.conversation import OpenAI
from tools.ai.stadif import StableDiffAI
from tools.ai.sdapi import SDAI
from tools.states import DAImage, SDImage, Text, MJImage, SDVideo
from tools.utils import config, load_params, split_into_chunks

logger = logging.getLogger(__name__)
router = Router()
openai = OpenAI()
stable_diff_ai = StableDiffAI()
sd_ai = SDAI()
params = load_params("params.json")
params_file = "params.json"
image_generators = [Midjourney(params_file, i) for i in range(10)]


@router.message(F.text.startswith("@naastyyaabot"))
async def ask(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.get)
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logger.info("%s", message)
        text = html.escape(message.text)
        escaped_text = text.strip('@naastyyaabot ')

        # Generate response
        replay_text, total_tokens = await openai.get_chat_response(uid, escaped_text)

        chunks = split_into_chunks(replay_text)
        for i, chunk in enumerate(chunks):
            try:
                if i == 0:
                    await message.reply(chunk, parse_mode=None)
            except Exception as err:
                try:
                    logger.info('From try in for index chunks: %s', err)
                    await message.reply(chunk + str(err), parse_mode=None)
                except Exception as error:
                    logger.info('Last exception from Core: %s', error)
                    await message.reply(str(error), parse_mode=None)


@router.message(Text.get, F.reply_to_message.from_user.is_bot)
async def process_ask(message: types.Message) -> None:
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logger.info("%s", message)

        # Generate response
        replay_text, total_tokens = await openai.get_chat_response(uid, message.text)
        chunks = split_into_chunks(replay_text)
        for i, chunk in enumerate(chunks):
            try:
                if i == 0:
                    await message.reply(chunk, parse_mode=None)
            except Exception as err:
                try:
                    logger.info('From try in for index chunks: %s', err)
                    await message.reply(chunk + str(err), parse_mode=None)
                except Exception as error:
                    logger.info('Last exception from Core: %s', error)
                    await message.reply(str(error), parse_mode=None)


@router.message(F.text.startswith("Нарисуй: "))
async def paint(message: types.Message, state: FSMContext) -> None:
    await state.set_state(DAImage.get)
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logger.info("%s", message)
        text = html.escape(message.text)
        escaped_text = text.strip('Нарисуй: ')
        result = await openai.send_dalle(escaped_text)
        print(result)
        try:
            photo = result
            await message.reply_photo(types.URLInputFile(photo))
        except Exception as err:
            try:
                text = "Что-то пошло не по плану. Если в это сообщении нет ссылки на нужное изображение, попробуй еще раз.\n "
                logger.info('From try in Picture: %s', err)
                await message.reply(text, parse_mode=None)
            except Exception as error:
                logger.info('Last exception from Picture: %s', error)
                await message.reply(str(error), parse_mode=None)


@router.message(DAImage.get)
async def process_paint(message: types.Message, state: FSMContext) -> None:
    await state.set_state(DAImage.result)
    logger.info("%s", message)


@router.message(F.text.startswith("Отобрази: "))
async def draw(message: types.Message, state: FSMContext) -> None:
    await state.set_state(MJImage.get)
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logger.info("%s", message)
        text = html.escape(message.text)
        escaped_text = text.strip('Отобрази: ')
        image_generator = random.choice(image_generators)
        resp = await image_generator.get_images(escaped_text)
        logger.info("RESPONSE FROM IMAGE GENERA %s", resp)
        try:
            photo = resp[0]['url']
            logger.info("OK GET RESULT PHOTO %s", photo)
            uuid = resp[0]['uuid']
            logger.info("OK GET RESULT UUID %s", uuid)
            message_id = resp[0]['id']
            logger.info("OK GET RESULT MESS ID %s", message_id)
            logger.info("OK GET RESULT IMGEN CHANNEL ID %s", image_generators.index(image_generator))
            await state.update_data(msg_id=message_id)
            await state.update_data(image_generator=image_generators.index(image_generator))
            await state.update_data(uuid=uuid)
            builder = InlineKeyboardBuilder()
            for i in range(1, 5):
                print(image_generators.index(image_generator))
                builder.add(types.InlineKeyboardButton(text=f"Upscale {i}", callback_data=f"ups:{i}"))
            builder.adjust(4)
            await message.reply_photo(photo=types.URLInputFile(photo), caption="какое изображение будет увеличивать?", reply_markup=builder.as_markup(resize_keyboard=True))
        except Exception as err:
            try:
                text = "Не удалось получить картинку. Попробуйте еще раз.\n "
                logger.info('From try in Picture: %s', err)
                await message.reply(text, parse_mode=None)
            except Exception as error:
                logger.info('Last exception from Picture: %s', error)
                await message.reply(str(error), parse_mode=None)


@router.message(MJImage.get)
async def process_draw(message: types.Message, state: FSMContext) -> None:
    await state.set_state(MJImage.result)
    logger.info("%s", message)


@router.message(F.text.startswith("Представь: "))
async def imagine(message: types.Message, state: FSMContext) -> None:
    await state.set_state(SDImage.get)
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logger.info("%s", message)
        text = html.escape(message.text)
        escaped_text = text.strip('Представь: ')
        result = await sd_ai.s2sdapi(escaped_text)
        logger.info("Result: %s", result)
        text = "⏳Время генерации: " + str(result['seed'])
        try:
            base64_image = result['image']
            image_data = base64.b64decode(base64_image)
            image_stream = io.BytesIO(image_data)
            image = Image.open(image_stream)
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp:
                image.save(temp, format='JPEG')
                await message.reply_photo(photo=temp.name, caption=text)
        except Exception as err:
            try:
                text = "Не удалось получить картинку. Попробуйте еще раз.\n "
                logger.info('From try in SD Picture: %s', err)
                await message.answer(text + result['output'][0], parse_mode=None)
            except Exception as error:
                logger.info('Last exception from SD Picture: %s', error)
                await message.answer(str(error), parse_mode=None)


@router.message(SDImage.get)
async def process_imagine(message: types.Message, state: FSMContext) -> None:
    await state.set_state(SDImage.result)
    logger.info("%s", message)


@router.message(F.text.startswith("Покажи: "))
async def show(message: types.Message, state: FSMContext) -> None:
    await state.set_state(SDVideo.get)
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logger.info("%s", message)
        text = html.escape(message.text)
        escaped_text = text.strip('Покажи: ')
        result = await stable_diff_ai.send2sd_video(escaped_text)
        logger.info("Result: %s", result)
        if result['status'] == 'processing':
            logger.info("PROCESSING")
            img_id = result['id']
            await asyncio.sleep(600)
            res = await stable_diff_ai.get_queued(img_id)
            logger.info("PROCCESSING Res: %s", res)
            video = res['output']
            await message.reply_video(types.URLInputFile(video))
        else:
            text = "⏳Время генерации: " + str(result['generationTime'])
            try:
                video = result['output'][0]
                await message.reply_video(types.URLInputFile(video), caption=text)
            except Exception as err:
                try:
                    text = "Не удалось получить картинку. Попробуйте еще раз.\n "
                    logger.info('From try in SD Picture: %s', err)
                    await message.answer(text + result['output'][0], parse_mode=None)
                except Exception as error:
                    logger.info('Last exception from SD Picture: %s', error)
                    await message.answer(str(error), parse_mode=None)


@router.message(SDVideo.get)
async def process_show(message: types.Message, state: FSMContext) -> None:
    await state.set_state(SDVideo.result)
    logger.info("%s", message)


@router.message(Command(commands="help"))
async def info_user(message: types.Message, l10n: FluentLocalization):
    await message.answer(l10n.format_value("help"))
