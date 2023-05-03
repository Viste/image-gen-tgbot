import asyncio
import logging
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import BotCommand, BotCommandScopeChat, InputMediaPhoto
from aioredis.client import Redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from core import setup_routers
from core.nedworker import get_random_prompts, delete_nearest_date
from middlewares.database import DbSessionMiddleware
from tools.ai_tools import StableDiffAI
from tools.language import Lang
from tools.utils import config
from tools.utils import fetch_admins, check_rights_and_permissions

engine = create_async_engine(url=config.db_url, echo=True)
redis_client = Redis(host=config.redis.host, port=config.redis.port, db=config.redis.db, decode_responses=True)
nasty = Bot(token=config.token, parse_mode="HTML")
stable_diff_ai = StableDiffAI()


async def set_bot_commands(bot: Bot, main_group_id: int):
    commands = [
        BotCommand(command="report", description="Пожаловаться на сообщение"),
        BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=main_group_id))


async def cron_task_wrapper():
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        await cron_task(session)


async def post_images(session):
    random_prompts = await get_random_prompts(session)

    url_list = []
    for prompt in random_prompts:
        url = await stable_diff_ai.gen_ned_img(prompt)
        url_list.append(url)

    if len(url_list) == 10:
        media = [InputMediaPhoto(image_url) for image_url in url_list]
        await nasty.send_media_group(chat_id=config.p_channel, media=media)


async def cron_task(session: AsyncSession):
    result = await delete_nearest_date(session)
    scheduled_date = result['date']
    scheduled_theme = result['theme']
    print(scheduled_date)
    print(scheduled_theme)
    # TODO: use theme returned from delete_nearest_date
    print("From cron task before IF")
    if scheduled_date <= datetime.now():
        await post_images(session)
        print("From cron after post")


async def run_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(cron_task_wrapper, 'interval', minutes=5)
    scheduler.start()

    while True:
        try:
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            break


async def main():
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout,
    )

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

    try:
        lang = Lang(config.lang)
    except ValueError:
        print(f"Error no localization found for language code: {config.lang}")
        return

    storage = RedisStorage(redis=redis_client)
    worker = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.GLOBAL_USER)
    router = setup_routers()
    worker.update.middleware(DbSessionMiddleware(session_pool=session_maker))
    worker.include_router(router)
    useful_updates = worker.resolve_used_update_types()
    await set_bot_commands(nasty, config.group_main)
    logging.info("Starting bot")
    await worker.start_polling(nasty, allowed_updates=useful_updates, lang=lang, handle_signals=True)


async def main_coro():
    main_task = asyncio.create_task(main())
    scheduler_task = asyncio.create_task(run_scheduler())
    await asyncio.gather(main_task, scheduler_task)


if __name__ == '__main__':
    try:
        asyncio.run(main_coro())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
