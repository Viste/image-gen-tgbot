from typing import Dict, List, Union
import json
import os
import requests
from aiogram import Bot, types
from aiogram.filters.callback_data import CallbackData
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner
from pydub import AudioSegment


class JSONObject:
    def __init__(self, dic):
        vars(self).update(dic)


cfg_file = open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf8')
config = json.loads(cfg_file.read(), object_hook=JSONObject)


class ClientSD:
    @staticmethod
    def send_sd_img_req(data: str):
        req = requests.post(config.deepai_api_url,
                            data={"text": data, "grid_size": 1, "width": 768, "height": 768},
                            headers={'api-key': config.deepai_api_key})
        result = req.json()
        return result


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


def trim_message(text: str) -> str:
    if text.startswith("?"):
        text = text.strip("?")
    return text.strip("\n")


def trim_name(text: str) -> str:
    if text.startswith("@naastyyaabot"):
        text = text.strip("@naastyyaabot")
    return text.strip("\n")


def trims(text: str) -> str:
    if text.startswith("Настя,"):
        text = text.strip("Настя,")
    return text.strip("\n")


def trim_cmd(text: str) -> str:
    if text.startswith("Нарисуй: "):
        text = text.strip("Нарисуй: ")
    return text.strip("\n")


def trim_image(text: str) -> str:
    if text.startswith("Представь: "):
        text = text.strip("Представь: ")
    return text.strip("\n")


def convert_oga_to_wav(filename: str):
    dst_wav = "/Users/viste/dev/nasty/tmp.wav"
    segment = AudioSegment.from_ogg(filename)
    wav_file = segment.export(dst_wav, format="wav")
    return dst_wav


def get_from_dalle(response: List[Dict[str, str]]) -> str:
    result = []
    for message in response:
        clear_message = message.get("url")
        result.append(clear_message)
    return """ """.join(result)


new_user_added = types.ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_invite_users=False,
    can_change_info=False,
    can_pin_messages=False,
)

user_allowed = types.ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_invite_users=True,
    can_change_info=False,
    can_pin_messages=False,
)
