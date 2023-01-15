from typing import Dict, List, Union
import aiohttp
import json
import os
from aiogram import Bot
from aiogram.filters.callback_data import CallbackData
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner

class JSONObject:
    def __init__(self, dict):
        vars(self).update(dict)

cfg_file = open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf8')
config = json.loads(cfg_file.read(), object_hook=JSONObject)

class DeleteMsgCallback(CallbackData, prefix="delmsg"):
    action: str
    entity_id: int
    message_ids: str  # Lists are not supported =(

async def fetch_admins(bot: Bot) -> Dict:
    result = {}
    admins: List[Union[ChatMemberOwner, ChatMemberAdministrator]]
    admins = await bot.get_chat_administrators(config.group_main)
    for admin in admins:
        if isinstance(admin, ChatMemberOwner):
            result[admin.user.id] = {"can_restrict_members": True}
        else:
            result[admin.user.id] = {"can_restrict_members": admin.can_restrict_members}
    return result


async def check_rights_and_permissions(bot: Bot, chat_id: int):
    chat_member_info = await bot.get_chat_member(chat_id=chat_id, user_id=bot.id)
    if not isinstance(chat_member_info, ChatMemberAdministrator):
        raise PermissionError("Мне нужны Админ-права")
    if not chat_member_info.can_restrict_members or not chat_member_info.can_delete_messages:
        raise PermissionError("Мне нужны эти права: 'restrict participants' и 'delete messages'")

class ClientChatGPT:

    @staticmethod
    async def send_data_chat_gpt(data: str):
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.api_key}"
            }
            data = {
                "model": "text-davinci-003",
                "prompt": data,
                "temperature": 0.9,
                "max_tokens": 512,
                "top_p": 1,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.6,
            }
            async with session.post(
                config.api_url,
                headers=headers,
                json=data
            ) as resp:
                return await resp.json()

def trim_message(text: str) -> str:
    if text.startswith("?"):
        text = text.strip("?")
    return text.strip("\n")

def result_to_text(response: List[Dict[str, str]]) -> str:
    result = []
    for message in response:
        clear_message = trim_message(
            message.get("text")
        )
        result.append(clear_message)
    return " ".join(result)
