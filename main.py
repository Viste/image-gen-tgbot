import asyncio
import logging
import sys
import base64
import uuid
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import BotCommand, BotCommandScopeChat, InputMediaPhoto
from aiogram.types.input_file import BufferedInputFile
from aioredis.client import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fluent.runtime import FluentLocalization, FluentResourceLoader
from pathlib import Path

from tools.ai.oairaw import OAI
from tools.ai.sdapi import SDAI
from core import setup_routers
from database.nedworker import get_random_prompts, delete_nearest_date, get_nearest_date, mark_as_posted
from middlewares.database import DbSessionMiddleware
from middlewares.l10n import L10nMiddleware
from tools.utils import config
from tools.utils import fetch_admins, check_rights_and_permissions

redis_client = Redis(host=config.redis.host, port=config.redis.port, db=config.redis.db, decode_responses=True)
nasty = Bot(token=config.token, parse_mode="HTML")
stable_diff_ai = SDAI()
oai = OAI()
engine = create_async_engine(url=config.db_url, echo=True, echo_pool=False, pool_size=50, max_overflow=30, pool_timeout=30, pool_recycle=3600)
session_maker = async_sessionmaker(engine, expire_on_commit=False)
db_middleware = DbSessionMiddleware(session_pool=session_maker)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", stream=sys.stdout)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot, main_group_id: int):
    commands = [BotCommand(command="report", description="Пожаловаться на сообщение"), BotCommand(command="help", description="Помощь"), ]
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=main_group_id))


async def cron_task_wrapper():
    async with session_maker() as session:
        await cron_task(session)


async def generate_image_list(session):
    random_prompts = await get_random_prompts(session)

    image_list = []
    prompt_index = 0
    while len(image_list) < 10 and prompt_index < len(random_prompts):
        prompt = random_prompts[prompt_index]
        try:
            base64_image = await stable_diff_ai.neda_gen(prompt['prompt'])
            image_bytes = base64.b64decode(base64_image)
            image_list.append(image_bytes)
        except IndexError as e:
            print(f"Error generating image for prompt '{prompt}': {e}")
        finally:
            prompt_index += 1

    logger.info(f"Generated {len(image_list)} images")
    return image_list, [prompt['id'] for prompt in random_prompts]


async def send_media_group(image_list):
    prompt = "Make a beautiful description for the post in the public telegram, the post attached 10 pictures of beautiful girls. the maximum length of text 1024 characters!"
    result = await oai.get_synopsis(prompt)
    res = result[:1024]
    logger.info(result)
    if len(image_list) >= 1:
        media = [InputMediaPhoto(media=BufferedInputFile(image, filename=f"{uuid.uuid4()}.jpg"), caption=res if i == 0 else None) for i, image in enumerate(image_list)]
        await nasty.send_media_group(chat_id=config.post_channel, media=media)
    else:
        logger.error("The number of images is less than 1.")


async def post_images(session):
    url_list, prompts = await generate_image_list(session)
    await send_media_group(url_list)
    await mark_as_posted(session, prompts)


async def cron_task(session: AsyncSession):
    result = await get_nearest_date(session)
    scheduled_date = result['date']
    scheduled_theme = result['theme']
    scheduled_id = result['id']

    logger.info("%s", scheduled_date)
    logger.info("%s", scheduled_theme)
    print("CR0N TasK BeFoRE IF")
    now = datetime.now().replace(second=0, microsecond=0)
    if scheduled_date == now:
        await post_images(session)
        await delete_nearest_date(session, scheduled_id)
        logger.info("FR0M CR0N after P0ST")


async def main():
    locales_dir = Path(__file__).parent.joinpath("locales")
    l10n_loader = FluentResourceLoader(str(locales_dir) + "/{locale}")
    l10n = FluentLocalization(["ru"], ["strings.ftl", "errors.ftl"], l10n_loader)

    try:
        await check_rights_and_permissions(nasty, config.group_main)
    except (TelegramAPIError, PermissionError) as error:
        error_msg = f"Error with main group: {error}"
        try:
            await nasty.send_message(config.group_reports, error_msg)
        finally:
            print(error_msg)
            return

    try:
        result = await fetch_admins(nasty)
    except TelegramAPIError as error:
        error_msg = f"Error fetching main group admins: {error}"
        try:
            await nasty.send_message(config.group_reports, error_msg)
        finally:
            print(error_msg)
            return
    config.admins = result

    storage = RedisStorage(redis=redis_client)
    worker = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.USER_IN_CHAT)
    router = setup_routers()
    worker.update.middleware(db_middleware)
    worker.update.middleware(L10nMiddleware(l10n))
    worker.include_router(router)
    useful_updates = worker.resolve_used_update_types()
    await set_bot_commands(nasty, config.group_main)
    logging.info("Starting bot")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(cron_task_wrapper, 'interval', minutes=1)
    scheduler.start()

    await worker.start_polling(nasty, allowed_updates=useful_updates, handle_signals=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
