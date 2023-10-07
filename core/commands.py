import html
import logging
import random

from aiogram import types, F, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tools.ai.MJWorker import Midjourney
from tools.ai.conversation import OpenAI
from tools.ai.stadif import StableDiffAI
from tools.states import DAImage, SDImage, Text, MJImage
from tools.utils import config, load_params, split_into_chunks

logger = logging.getLogger(__name__)
router = Router()
openai = OpenAI()
stable_diff_ai = StableDiffAI()
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
async def draw(message: types.Message, state: FSMContext) -> None:
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
async def process_imagine(message: types.Message, state: FSMContext) -> None:
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
        result = await stable_diff_ai.send2sdapi(escaped_text)
        logger.info("Result: %s", result)
        text = "⏳Время генерации: " + str(result['generationTime']) \
               + " секунд. 🌾Зерно: " \
               + str(result['meta']['seed']) \
               + ", 🦶Шаги: " + str(result['meta']['steps'])
        try:
            photo = result['output'][0]
            await message.reply_photo(types.URLInputFile(photo), caption=text)
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


@router.message(Command(commands="help"))
async def info(message: types.Message):
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        text = ("🤖НАСТЯ - ВАШ ПОМОЩНИК В СЕТИ!\n" 
                "\n"
                "Проекты участия:\n"
                "Нейронка Каждый День\n"
                "Paperfunk Chat\n"
                "PPRFNK Технократы\n"
                "\n"
                "Безопасность:\n"
                "🚫Если заметили нарушителя, дайте знать: /report.\n"
                "❌Отменить действие: /cancel.\n"
                "\n"
                "Общение:\n"
                "Хотите задать вопрос? Обращайтесь: @naastyyaabot.\n"
                "\n"
                "🎨DaLLE2:\n"
                "Нарисуй: ....\n"
                "\n"
                "🌌Stable Diffusio (SD):\n"
                "Представь: ....\n"
                "\n"
                "🌠Midjourney:\n"
                "Отобрази: ...\n"
                "Ожидайте примерно 3 минуты. После этого будут представлены 4 варианта изображения, один из которых вы сможете увеличить для лучшего просмотра."
                "\n"
                "\n"
                "Автор: @vistee, Помогал: @paperclipdnb")
        await message.reply(text, parse_mode=None)
