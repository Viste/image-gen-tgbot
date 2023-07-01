import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta

import aiohttp
from dateutil.parser import parse

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
            async with session.get('https://discord.com/api/v10/channels/{self.channelid}/messages?limit={10}',
                                   headers=headers) as resp:
                logger.info(
                    f'Sending GET request to https://discord.com/api/v10/channels/{self.channelid[self.index]}/messages?limit={10}')
                try:
                    result = await resp.text()
                    logger.info(f'Received response: {result}')
                    return json.loads(result)
                except json.JSONDecodeError:
                    logger.error("Error: Invalid JSON response")
                    return []

    async def collecting_results(self):
        message_list = await self.retrieve_messages()
        for message in message_list:
            try:
                if (message['author']['username'] == 'Midjourney Bot') and ('**' in message['content']):
                    if len(message['attachments']) > 0:
                        if (message['attachments'][0]['filename'][-4:] == '.png') or (
                                '(Open on website for full quality)' in message['content']):
                            id = message['id']
                            prompt = message['content'].split('**')[1].split(' --')[0]
                            url = message['attachments'][0]['url']
                            filename = message['attachments'][0]['filename']
                            uuid = filename.split('_')[-1].split('.')[0]
                            self.images.append({'id': id, 'prompt': prompt, 'url': url, 'uuid': uuid})
                            self.latest_image_timestamp = parse(message["timestamp"])
            except KeyError:
                logging.info("Error: Message does not contain expected elements")

    async def send_prompt(self, prompt):
        header = {
            'authorization': self.authorization
        }
        payload = {'type': 2, 'application_id': self.application_id, 'guild_id': self.guild_id,
                   'channel_id': self.channelid[self.index], 'session_id': self.session_id,
                   'data': {
                       'version': self.version, 'id': self.id, 'name': 'imagine', 'type': 1,
                       'options': [{
                           'type': 3, 'name': 'prompt', 'value': str(prompt)
                       }], 'attachments': []}
                   }
        logging.info('Payload: %s', payload)
        async with aiohttp.ClientSession() as session:
            max_retries = 10
            for _ in range(max_retries):
                async with session.post('https://discord.com/api/v9/interactions', json=payload,
                                        headers=header) as resp:
                    logger.info(f'Received response: {resp.text}')
                    if resp.status == 204:
                        logging.info(f'prompt {prompt} successfully sent!')
                        break
                    else:
                        logging.info(f'Failed to send prompt request after {max_retries} retries')
                await asyncio.sleep(3)

    async def get_images(self, prompt):
        await self.send_prompt(prompt)
        await self.collecting_results()
        return self.images

    async def send_upscale_request(self, message_id, number, uuid):
        header = {'authorization': self.authorization}
        payload = {'type': 3,
                   'application_id': self.application_id,
                   'guild_id': self.guild_id,
                   'channel_id': self.channelid[self.index],
                   'session_id': self.session_id,
                   "message_flags": 0,
                   "message_id": message_id,
                   "data": {"component_type": 2, "custom_id": f"MJ::JOB::upsample::{number}::{uuid}"}}
        async with aiohttp.ClientSession() as session:
            max_retries = 10
            for _ in range(max_retries):
                async with session.post('https://discord.com/api/v9/interactions', json=payload,
                                        headers=header) as resp:
                    logger.info(f'Received response: {resp.text}')
                    if resp.status == 204:
                        logging.info(
                            f'Upscale request for message_id {message_id} and number {number} successfully sent!')
            else:
                logging.info(f'Failed to send upscale request after {max_retries} retries')
        logging.info(f'Upscale request for message_id {message_id} and number {number} successfully sent!')

    async def upscale(self, message_id, number, uuid):
        await self.send_upscale_request(message_id, number, uuid)
        initial_image_timestamp = self.latest_image_timestamp

        # Wait for new image to appear
        max_wait_time = 300
        wait_time = 0

        while wait_time < max_wait_time:
            await self.collecting_results()
            current_image_timestamp = self.latest_image_timestamp
            if current_image_timestamp and current_image_timestamp > initial_image_timestamp:
                break
            await asyncio.sleep(1)
            wait_time += 1

        if current_image_timestamp and current_image_timestamp > initial_image_timestamp:
            latest_image = self.images[-1]
            latest_image_url = latest_image['url']
        else:
            latest_image_url = None
        return latest_image_url
