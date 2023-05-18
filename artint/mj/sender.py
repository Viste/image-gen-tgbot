import json

import aiohttp
from aiohttp import ClientResponse


class Sender:

    def __init__(self,
                 params,
                 index, flag):

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
        try:
            self.flag = int(flag)
        except ValueError:
            self.flag = 0
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

    # noinspection PyAssignmentToLoopOrWithParameter
    async def send(self, prompt):
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
                       'options': [{'type': 3, 'name': 'prompt', 'value': str(prompt) + ' ' + self.flags[self.flag]}],
                       'attachments': []}
                   }

        async with aiohttp.ClientSession() as session:
            req: ClientResponse
            async with session.post('https://discord.com/api/v9/interactions', json=payload, headers=header) as req:
                while req.status != 204:
                    async with session.post('https://discord.com/api/v9/interactions', json=payload, headers=header) as req:
                        pass

        print('prompt [{}] successfully sent!'.format(prompt))
