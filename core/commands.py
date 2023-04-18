import logging

from aiogram import types, F, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from misc.ai_tools import OpenAI, StableDiffAI
from misc.states import DAImage, SDImage, Text, Video
from misc.utils import config, trim_image, trim_video
from misc.utils import trim_name, trim_cmd, split_into_chunks

logger = logging.getLogger("__name__")
router = Router()

openai = OpenAI()
stable_diff_ai = StableDiffAI()


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
        replay_text, total_tokens = await openai.get_chat_response(uid, trimmed)

        chunks = split_into_chunks(replay_text)
        for index, chunk in enumerate(chunks):
            try:
                if index == 0:
                    await message.reply(chunk, parse_mode=None)
            except Exception as err:
                try:
                    logging.info('From try in for index chunks: %s', err)
                    await message.reply(chunk + err, parse_mode=None)
                except Exception as error:
                    logging.info('Last exception from Core: %s', error)
                    await message.reply(error, parse_mode=None)


@router.message(Text.get, F.reply_to_message.from_user.is_bot)
async def process_ask(message: types.Message) -> None:
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)

        # Generate response
        replay_text, total_tokens = await openai.get_chat_response(uid, message.text)
        chunks = split_into_chunks(replay_text)
        for index, chunk in enumerate(chunks):
            try:
                if index == 0:
                    await message.reply(chunk, parse_mode=None)
            except Exception as err:
                try:
                    logging.info('From try in for index chunks: %s', err)
                    await message.reply(chunk + err, parse_mode=None)
                except Exception as error:
                    logging.info('Last exception from Core: %s', error)
                    await message.reply(error, parse_mode=None)


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
        result = await openai.send_dalle(trimmed)
        try:
            photo = result
            await message.reply_photo(photo)
        except Exception as err:
            try:
                text = "Не удалось получить картинку. Попробуйте еще раз.\n "
                logging.info('From try in Picture: %s', err)
                await message.reply(text + result, parse_mode=None)
            except Exception as error:
                logging.info('Last exception from Picture: %s', error)
                await message.reply(error, parse_mode=None)


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
        trimmed = trim_image(message.text)
        result = await stable_diff_ai.send_sdapi(trimmed)
        print(result)
        text = "⏳Время генерации: " + str(result['generationTime']) \
               + " секунд. 🌾Зерно: " \
               + str(result['meta']['seed']) \
               + ", 💃Модель: " + str(result['meta']['model']) \
               + ", 🦶Шаги: " + str(result['meta']['steps'])
        try:
            photo = result['output'][0]
            await message.reply_photo(photo, caption=text)
        except Exception as err:
            try:
                text = "Не удалось получить картинку. Попробуйте еще раз.\n "
                logging.info('From try in SD Picture: %s', err)
                await message.answer(text + result['output'][0], parse_mode=None)
            except Exception as error:
                logging.info('Last exception from SD Picture: %s', error)
                await message.answer(error, parse_mode=None)


@router.message(SDImage.get)
async def process_imagine(message: types.Message, state: FSMContext) -> None:
    await state.set_state(SDImage.result)
    logging.info("%s", message)


@router.message(F.text.startswith("Замути, "))
async def imagine(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Video.get)
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        trimmed = trim_video(message.text)
        result = await stable_diff_ai.send_sd_video(trimmed)
        print(result)
        try:
            video = result['output'][0]
            await message.reply_video(video)
        except Exception as err:
            try:
                text = "Не удалось получить картинку. Попробуйте еще раз.\n "
                logging.info('From try in SD Picture: %s', err)
                await message.reply(text + result['output'][0], parse_mode=None)
            except Exception as error:
                logging.info('Last exception from SD Picture: %s', error)
                await message.answer(error, parse_mode=None)


@router.message(Video.get)
async def process_imagine(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Video.result)
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
