import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from core import setup_routers
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import BotCommand, BotCommandScopeChat
from misc.utils import fetch_admins, check_rights_and_permissions
from misc.utils import config
from misc.language import Lang


async def set_bot_commands(bot: Bot, main_group_id: int):
    commands = [
        BotCommand(command="report", description="Пожаловаться на сообщение"),
        BotCommand(command="dream", description="Напиши что хочешь нарисовать? Я передам это нейросети SD"),
        BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=main_group_id))


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout,
    )

    bot = Bot(token=config.token, parse_mode="HTML")
    worker = Dispatcher()

    try:
        await check_rights_and_permissions(bot, config.group_main)
    except (TelegramAPIError, PermissionError) as error:
        error_msg = f"Error with main group: {error}"
        try:
            await bot.send_message(config.group_reports, error_msg)
        finally:
            print(error_msg)
            return

    try:
        result = await fetch_admins(bot)
    except TelegramAPIError as error:
        error_msg = f"Error fetching main group admins: {error}"
        try:
            await bot.send_message(config.group_reports, error_msg)
        finally:
            print(error_msg)
            return
    config.admins = result

    try:
        lang = Lang(config.lang)
    except ValueError:
        print(f"Error no localization found for language code: {config.lang}")
        return

    router = setup_routers()
    worker.include_router(router)
    useful_updates = worker.resolve_used_update_types()
    await set_bot_commands(bot, config.group_main)
    logging.info("Starting bot")
    await worker.start_polling(bot, allowed_updates=useful_updates, lang=lang)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
