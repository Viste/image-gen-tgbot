import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BotCommand, BotCommandScopeChat
from celery import Celery

from core import setup_routers
from misc.language import Lang
from misc.tasks import send_davinci
from misc.utils import config
from misc.utils import fetch_admins, check_rights_and_permissions

nasty = Bot(token=config.token, parse_mode="HTML")

app = Celery('manager', broker=config.celery_url, backend=config.celery_backend)
app.autodiscover_tasks()
app.conf.update(
    result_expires=3600,
    result_backend_transport_options={
      'retry_policy': {'timeout': 5.0},
    }
)
conversations = {}


async def set_bot_commands(bot: Bot, main_group_id: int):
    commands = [
        BotCommand(command="report", description="Пожаловаться на сообщение"),
        BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=main_group_id))


def conversation_tracking(text_message, user_id):
    # Get the last 10 conversations and responses for this user
    user_conversations = conversations.get(user_id, {'conversations': [], 'responses': []})
    user_messages = user_conversations['conversations'][-9:] + [text_message]
    user_responses = user_conversations['responses'][-9:]

    # Store the updated conversations and responses for this user
    conversations[user_id] = {'conversations': user_messages, 'responses': user_responses}

    # Construct the full conversation history in the "human: bot: " format
    conversation_history = ""
    for i in range(min(len(user_messages), len(user_responses))):
        conversation_history += f"human: {user_messages[i]}\nНастя: {user_responses[i]}\n"

    if conversation_history == "":
        conversation_history = "human:{}\nНастя:".format(text_message)
    else:
        conversation_history += "human:{}\nНастя:".format(text_message)

    # Generate response
    print(conversation_history)
    task = send_davinci.apply_async(args=[conversation_history])
    response = task.get()

    # Add the response to the user's responses
    user_responses.append(response)
    # Store the updated conversations and responses for this user
    conversations[user_id] = {'conversations': user_messages, 'responses': user_responses}

    return response


async def main():
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

    worker = Dispatcher()
    router = setup_routers()
    worker.include_router(router)
    useful_updates = worker.resolve_used_update_types()
    await set_bot_commands(nasty, config.group_main)
    logging.info("Starting bot")
    await worker.start_polling(nasty, allowed_updates=useful_updates, lang=lang)


if __name__ == '__main__':
    try:
        asyncio.run(main())
        app.start()
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
