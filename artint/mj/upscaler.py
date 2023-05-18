import json
import logging

import aiohttp

logger = logging.getLogger("__name__")


class Upscaler:
    def __init__(self, params, index):
        self.session_id = None
        self.version = None
        self.id = None
        self.flags = None
        self.guild_id = None
        self.application_id = None
        self.authorization = None
        self.channelid = None
        self.index = index
        self.params = params
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
    async def send(self, message_id, number, uuid):
        header = {'authorization': self.authorization}
        payload = {'type': 3,
                   'application_id': self.application_id,
                   'guild_id': self.guild_id,
                   'channel_id': self.channelid[self.index],
                   'session_id': self.session_id,
                   "message_flags": 0,
                   "message_id": message_id,
                   "data": {"component_type": 2, "custom_id": f"MJ::JOB::upsample::{number}::{uuid}"}}

        logger.info(f"Upscale request payload: {payload}")
        async with aiohttp.ClientSession() as session:
            async with session.post('https://discord.com/api/v9/interactions',
                                    json=payload,
                                    headers=header) as req:
                while req.status != 204:
                    logger.info(f"Upscale request status code: {req.status}")
                    response_text = await req.text()
                    logger.info(f"Upscale request response: {response_text}")
                    async with session.post('https://discord.com/api/v9/interactions',
                                            json=payload,
                                            headers=header) as req:
                        pass

        logging.info('Upscale request for message_id [{}] and number [{}] successfully sent!'.format(message_id, number))
