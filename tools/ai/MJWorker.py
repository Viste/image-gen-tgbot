import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta

import aiohttp

logger = logging.getLogger(__name__)


class Midjourney:
    def __init__(self, params, index):
        self.latest_image_timestamp = datetime.now(timezone.utc) - timedelta(days=1)
        self.images = []
        self.id = None
        self.application_id = None
        self.guild_id = None
        self.session_id = None
        self.version = None
        self.flags = None
        self.authorization = None
        self.channelid = None
        self.params = params
        self.index = index
        self.sender_initializer()

    def sender_initializer(self):
        with open(self.params, "r") as json_file:
            params = json.load(json_file)

        self.channelid = params['channelid']
        self.authorization = params['authorization']
        self.application_id = params['application_id']
        self.guild_id = params['guild_id']
        self.session_id = params['session_id']
        self.version = params['version']
        self.id = params['id']
        self.flags = params['flags']

    async def retrieve_messages(self):
        headers = {
                'authorization': self.authorization
            }
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://discord.com/api/v10/channels/{self.channelid[self.index]}/messages?limit=10',
                                   headers=headers) as resp:
                logger.info(
                    f'Sending GET request to https://discord.com/api/v10/channels/{self.channelid[self.index]}/messages?limit=10')
                try:
                    result = await resp.text()
                    logger.info(f'Received response: {result}')
                    return json.loads(result)
                except json.JSONDecodeError:
                    logger.error("Error: Invalid JSON response")
                    return []

    async def collecting_results(self, promt):
        message_list = await self.retrieve_messages()
        for message in message_list:
            try:
                if (message.get("author", {}).get("username") == "Midjourney Bot") and (f"{promt}" in message.get("content", "")):
                    if len(message.get("attachments", [])) > 0:
                        if (message["attachments"][0].get("filename", "")[-4:] == ".png") or ("(Open on website for full quality)" in message.get("content", "")):
                            id = message.get("id")
                            prompt = (message.get("content", "").split("**")[1].split(" --")[0])
                            url = message["attachments"][0].get("url")
                            filename = message["attachments"][0].get("filename")
                            uuid = filename.split("_")[-1].split(".")[0]
                            self.images.append({"id": id, "prompt": prompt, "url": url, "uuid": uuid})
            except KeyError:
                logger.info("Error: Message does not contain expected elements")

    async def send_prompt(self, prompt):
        header = {
            'authorization': self.authorization
            }
        payload = {'type': 2,
                   'application_id': self.application_id,
                   'guild_id': self.guild_id,
                   'channel_id': self.channelid[self.index],
                   'session_id': self.session_id,
                   'data': {
                       'version': self.version,
                       'id': self.id,
                       'name': 'imagine',
                       'type': 1,
                       'options': [{
                           'type': 3, 'name': 'prompt', 'value': str(prompt)
                           }],
                       'attachments': []}}
        logger.info('Payload: %s', payload)
        async with aiohttp.ClientSession() as session:
            max_retries = 10
            for _ in range(max_retries):
                async with session.post('https://discord.com/api/v9/interactions', json=payload,
                                        headers=header) as resp:
                    logger.info(f'Received response: {resp.text}')
                    if resp.status == 204:
                        logger.info(f'prompt {prompt} successfully sent!')
                        break
                    else:
                        logger.info(f'Failed to send prompt request after {max_retries} retries')
                await asyncio.sleep(3)

    async def get_images(self, prompt):
        await self.send_prompt(prompt)
        await asyncio.sleep(120)
        await self.collecting_results(prompt)
        return self.images

    async def send_upscale_request(self, message_id, number, uuid):
        header = {"authorization": self.authorization}
        payload = {
            "type": 3,
            "application_id": self.application_id,
            "guild_id": self.guild_id,
            "channel_id": self.channelid[self.index],
            "session_id": self.session_id,
            "message_flags": 0,
            "message_id": message_id,
            "data": {
                "component_type": 2,
                "custom_id": f"MJ::JOB::upsample::{number}::{uuid}",
                },
            }
        async with aiohttp.ClientSession() as session:
            max_retries = 10
            for _ in range(max_retries):
                async with session.post("https://discord.com/api/v9/interactions", json=payload, headers=header) as resp:
                    logger.info(f"Received response: {resp.text}")
                    if resp.status == 204:
                        logger.info(f"Upscale request for message_id {message_id} and number {number} successfully sent!")
                        break
                    else:
                        logger.info(f"Failed to send upscale request after {max_retries} retries")
                await asyncio.sleep(3)

    async def upscale(self, message_id, number, uuid):
        await self.send_upscale_request(message_id, number, uuid)
        await asyncio.sleep(20)

        message_list = await self.retrieve_messages()
        for message in reversed(message_list):
            try:
                if (message.get("author", {}).get("username") == "Midjourney Bot") and (f"Image #{number}" in message.get("content", "")):
                    if len(message.get("attachments", [])) > 0:
                        if (message["attachments"][0].get("filename", "")[-4:] == ".png") or ("(Open on website for full quality)" in message.get("content", "")):
                            ref_id = message["message_reference"].get("message_id")
                            if ref_id == message_id:
                                return message["attachments"][0].get("url")
            except KeyError:
                logger.info("Error: Message does not contain expected elements")
        return None
