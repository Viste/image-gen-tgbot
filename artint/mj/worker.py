import asyncio
import json
import logging
import re
from datetime import datetime, timezone, timedelta

import aiohttp
import pandas as pd
from dateutil.parser import parse

logger = logging.getLogger(__name__)


class MidjourneyBot:
    def __init__(self, params, index):
        self.params = params
        self.index = index
        self.sender_initializer()
        self.latest_image_timestamp = datetime.now(timezone.utc) - timedelta(days=1)
        self.df = pd.DataFrame(columns=['prompt', 'url', 'filename', 'uuid'])

    def sender_initializer(self):
        with open(self.params, "r") as json_file:
            params = json.load(json_file)
        self.channelid = params['channelid'][self.index]
        self.authorization = params['authorization']
        self.headers = {'authorization': self.authorization}
        self.application_id = params['application_id']
        self.guild_id = params['guild_id']
        self.session_id = params['session_id']
        self.version = params['version']
        self.id = params['id']

    async def retrieve_messages(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://discord.com/api/v10/channels/{self.channelid}/messages?limit={10}',
                                   headers=self.headers) as resp:
                try:
                    result = await resp.text()
                    return json.loads(result)
                except json.JSONDecodeError:
                    logging.info("Error: Invalid JSON response")
                    return []

    async def collecting_results(self):
        message_list = await self.retrieve_messages()
        self.awaiting_list = pd.DataFrame(columns=['prompt', 'status'])
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
                            if id not in self.df.index:
                                self.df.loc[id] = [prompt, url, filename, uuid]
                                self.latest_image_timestamp = parse(message["timestamp"])
                        else:
                            id = message['id']
                            prompt = message['content'].split('**')[1].split(' --')[0]
                            if ('(fast)' in message['content']) or ('(relaxed)' in message['content']):
                                try:
                                    status = re.findall("(\w*%)", message['content'])[0]
                                except IndexError:
                                    status = 'unknown status'
                            self.awaiting_list.loc[id] = [prompt, status]
                    else:
                        id = message['id']
                        prompt = message['content'].split('**')[1].split(' --')[0]
                        if '(Waiting to start)' in message['content']:
                            status = 'Waiting to start'
                        self.awaiting_list.loc[id] = [prompt, status]
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
                           'type': 3, 'name': 'prompt', 'value': str(prompt) + ' '
                       }], 'attachments': []}
                   }
        async with aiohttp.ClientSession() as session:
            max_retries = 10
            for _ in range(max_retries):
                async with session.post('https://discord.com/api/v9/interactions', json=payload,
                                        headers=header) as resp:
                    if resp.status == 204:
                        logging.info(f'prompt {prompt} successfully sent!')
                        break
                    else:
                        logging.info(f'Failed to send upscale request after {max_retries} retries')
                await asyncio.sleep(3)

    async def get_images(self, prompt):
        await self.send_prompt(prompt)
        await self.collecting_results()
        return self.df.reset_index().rename(columns={'index': 'message_id'})

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
                async with aiohttp.ClientSession() as session:
                    async with session.post('https://discord.com/api/v9/interactions', json=payload,
                                            headers=header) as resp:
                        if resp.status == 204:
                            pass
            else:
                logging.info(f'Failed to send prompt after {max_retries} retries')
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
            latest_image_id = self.df.index[-1]
            latest_image_url = self.df.loc[latest_image_id].url
        else:
            latest_image_url = None
        return latest_image_url
