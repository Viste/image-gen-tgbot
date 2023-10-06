import asyncio
import logging
import signal
import sys
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import BotCommand, BotCommandScopeChat, InputMediaPhoto
from aioredis.client import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fluent.runtime import FluentLocalization, FluentResourceLoader
from pathlib import Path

from tools.ai.oairaw import OAI
from tools.ai.stadif import StableDiffAI
from core import setup_routers
from database.nedworker import get_random_prompts, delete_nearest_date, get_nearest_date, mark_as_posted
from middlewares.database import DbSessionMiddleware
from middlewares.l10n import L10nMiddleware
from tools.utils import config
from tools.utils import fetch_admins, check_rights_and_permissions

redis_client = Redis(host=config.redis.host, port=config.redis.port, db=config.redis.db, decode_responses=True)
nasty = Bot(token=config.token, parse_mode="HTML")
stable_diff_ai = StableDiffAI()
oai = OAI()
scheduler = AsyncIOScheduler()
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

scheduler.add_job(cron_task_wrapper, 'interval', minutes=60)


def handle_signals(loop, scheduler_task):
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for sig in signals:
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s, loop, scheduler_task)))


async def generate_url_list(session):
    random_prompts = await get_random_prompts(session)

    url_list = []
    prompt_index = 0
    while len(url_list) < 10 and prompt_index < len(random_prompts):
        prompt = random_prompts[prompt_index]
        try:
            url = await stable_diff_ai.gen_ned_img(prompt['prompt'])
            url_list.append(url)
        except IndexError as e:
            print(f"Error generating image URL for prompt '{prompt}': {e}")
        finally:
            prompt_index += 1

    logger.info(url_list)
    return url_list, [prompt['id'] for prompt in random_prompts]


async def send_media_group(url_list):
    prompt = "Make a beautiful description for the post in the public telegram, the post attached 10 pictures of beautiful girls. the maximum length of 1024 characters"
    result = await oai.get_synopsis(prompt)
    logger.info(result)
    if len(url_list) >= 1:
        media = [InputMediaPhoto(media=url, caption=result if i == 0 else None) for i, url in enumerate(url_list)]
        await nasty.send_media_group(chat_id=config.post_channel, media=media)
    else:
        logger.error("The number of URLs is less than 1.")


async def post_images(session):
    url_list, prompts = await generate_url_list(session)
    await send_media_group(url_list)
    await mark_as_posted(session, prompts)


async def cron_task(session: AsyncSession):
    result = await get_nearest_date(session)
    scheduled_date = result['date']
    scheduled_theme = result['theme']
    scheduled_id = result['id']

    print(scheduled_date)
    print(scheduled_theme)
    # TODO use theme returned from get_nearest_date
    print("From cron task before IF")
    if scheduled_date <= datetime.now():
        await post_images(session)
        await delete_nearest_date(session, scheduled_id)
        print("From cron after post")


async def run_scheduler_wrapper():
    while True:
        try:
            async with session_maker() as session:
                await run_scheduler(session)
        except (KeyboardInterrupt, SystemExit):
            break
        except Exception as e:
            logging.error(f"Error in run_scheduler_wrapper: {e}")
            try:
                await session.rollback()
            except Exception as rollback_error:
                logging.error(f"Error rolling back transaction: {rollback_error}")
            await asyncio.sleep(60)


async def run_scheduler(session: AsyncSession):
    while True:
        try:
            nearest_date = await get_nearest_date(session)
            if nearest_date:
                now = datetime.now()
                if now >= nearest_date['date']:
                    await cron_task_wrapper()
                    await asyncio.sleep(60)
                else:
                    sleep_time = (nearest_date['date'] - now).total_seconds()
                    await asyncio.sleep(sleep_time)
            else:
                logging.info("Table is empty. No nearest date found.")
                await asyncio.sleep(3600)  # Sleep for 1 hour before checking again
        except asyncio.CancelledError:
            break
        except Exception as e:
            logging.error(f"Error in run_scheduler: {e}")
            await asyncio.sleep(60)


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
    await worker.start_polling(nasty, allowed_updates=useful_updates, handle_signals=True)


async def shutdown(sign, loop, scheduler_task):
    logging.info(f"Received exit signal {sign.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    scheduler_task.cancel()

    for task in tasks:
        task.cancel()

    logging.info("Cancelling outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


async def main_coro():
    loop = asyncio.get_event_loop()

    main_task = asyncio.create_task(main())
    await main_task

    scheduler.start()

    scheduler_task = asyncio.create_task(run_scheduler_wrapper())
    handle_signals(loop, scheduler_task)

    results = await asyncio.gather(scheduler_task, return_exceptions=True)

    for task, result in zip([scheduler_task], results):
        if isinstance(result, Exception):
            logging.error(f"Task {task} raised an exception: {result}")

    for task in [scheduler_task]:
        if not task.done():
            task.cancel()


if __name__ == '__main__':
    try:
        asyncio.run(main_coro())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
