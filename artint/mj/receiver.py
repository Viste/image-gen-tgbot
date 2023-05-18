import json
import logging
import re
from datetime import datetime, timezone, timedelta

import aiohttp
import pandas as pd

logger = logging.getLogger("__name__")


class Receiver:

    def __init__(self, params, index):

        self.awaiting_list = None
        self.headers = None
        self.authorization = None
        self.channelid = None
        self.params = params
        self.index = index
        self.sender_initializer()
        self.latest_image_timestamp = datetime.now(timezone.utc) - timedelta(minutes=10)
        self.df = pd.DataFrame(columns=['prompt', 'url', 'filename', 'timestamp', 'is_downloaded'])

    def sender_initializer(self):

        with open(self.params, "r") as json_file:
            params = json.load(json_file)

        self.channelid = params['channelid'][self.index]
        self.authorization = params['authorization']
        self.headers = {'authorization': self.authorization}

    async def retrieve_messages(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://discord.com/api/v10/channels/{self.channelid}/messages?limit={10}', headers=self.headers) as resp:
                jsonn = await resp.json()
        return jsonn

    async def collecting_results(self):
        message_list = await self.retrieve_messages()
        self.awaiting_list = pd.DataFrame(columns=['prompt', 'status'])
        logging.info("COLLECTING RESULT")
        current_timestamp = datetime.now(timezone.utc)

        any_message_processed = False
        for message in message_list:
            message_timestamp = datetime.fromisoformat(message["timestamp"].rstrip("Z"))

            # Check if the message is not older than 10 minutes
            if (current_timestamp - message_timestamp) <= timedelta(minutes=10):
                any_message_processed = True
            # Process the message
            if (message['author']['username'] == 'Midjourney Bot') and ('**' in message['content']):
                message_timestamp = message["timestamp"]
                if len(message['attachments']) > 0:
                    if (message['attachments'][0]['filename'][-4:] == '.png') or ('(Open on website for full quality)' in message['content']):
                        message_id = message['id']
                        prompt = message['content'].split('**')[1].split(' --')[0]
                        url = message['attachments'][0]['url']
                        filename = message['attachments'][0]['filename']
                        if message_id not in self.df.index:
                            self.df.loc[message_id] = [prompt, url, filename, message_timestamp, 0]
                            self.latest_image_timestamp = message["timestamp"]

                    else:
                        message_id = message['id']
                        prompt = message['content'].split('**')[1].split(' --')[0]
                        if ('(fast)' in message['content']) or ('(relaxed)' in message['content']):
                            try:
                                status = re.findall("(\w*%)", message['content'])[0]
                            except:
                                status = 'unknown status'
                        self.awaiting_list.loc[message_id] = [prompt, status]

                else:
                    message_id = message['id']
                    prompt = message['content'].split('**')[1].split(' --')[0]
                    if '(Waiting to start)' in message['content']:
                        status = 'Waiting to start'
                    self.awaiting_list.loc[message_id] = [prompt, status]

            if not any_message_processed:
                logging.info("All messages are outdated. Breaking the loop.")
                return
