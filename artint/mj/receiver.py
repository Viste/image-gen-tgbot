import json
import re
from datetime import datetime, timezone, timedelta

import pandas as pd
import requests
from dateutil.parser import parse


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

    def retrieve_messages(self):
        r = requests.get(f'https://discord.com/api/v10/channels/{self.channelid}/messages?limit={10}', headers=self.headers)
        jsonn = json.loads(r.text)
        return jsonn

    def collecting_results(self):
        message_list = self.retrieve_messages()
        self.awaiting_list = pd.DataFrame(columns=['prompt', 'status'])
        print("COLLECTING RESULT")
        for message in message_list:
            print("Processing message:", message)
            if 'timestamp' not in message:
                print("Skipping message due to missing timestamp")
                continue
            if message['author']['username'] != 'Midjourney Bot':
                print("Skipping message due to different author")
                continue
            message_timestamp = parse(message["timestamp"])
            if message_timestamp <= self.latest_image_timestamp:
                print("Skipping message due to older timestamp")
                continue

            # Check if the message has already been processed
            message_id = message['id']
            if message_id in self.df.index:
                print(f"Skipping message {message_id} as it has already been processed")
                continue

            # Process the message
            if (message['author']['username'] == 'Midjourney Bot') and ('**' in message['content']):
                # Update the latest_image_timestamp
                self.latest_image_timestamp = max(self.latest_image_timestamp, message_timestamp)
                if len(message['attachments']) > 0:
                    if (message['attachments'][0]['filename'][-4:] == '.png') or ('(Open on website for full quality)' in message['content']):
                        message_id = message['id']
                        prompt = message['content'].split('**')[1].split(' --')[0]
                        url = message['attachments'][0]['url']
                        filename = message['attachments'][0]['filename']
                        timestamp = message['timestamp']
                        if id not in self.df.index:
                            self.df.loc[message_id] = [prompt, url, filename, timestamp, 0]
                            self.latest_image_timestamp = parse(message["timestamp"])

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
