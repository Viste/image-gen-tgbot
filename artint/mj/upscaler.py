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
        payload = {
            "type": 3,
            "application_id": "936929561302675456",
            "guild_id": "1107590351218294876",
            "channel_id": "1107591970173493268",
            "message_flags": 0,
            "message_id": "1108632106411773963",
            "session_id": "5ef23bcd47a40dd780f60007ce12acc7",
            "data": {
                "component_type": 2,
                "custom_id": "MJ::JOB::upsample::3::26adba4f-a22d-4269-ade0-d53152b421e8"
            }
        }

        logger.info(f"Upscale request payload: {payload}")
        async with aiohttp.ClientSession() as session:
            async with session.post('https://discord.com/api/v9/interactions',
                                    json=payload,
                                    headers=header) as req:
                while req.status != 204:
                    logger.info(f"Upscale request status code: {req.status}")
                    response_text = await req.text()
                    logger.info(f"Upscale request response: {response_text}")
                    async with session.post('https://discord.com/api/v9/interactions', json=payload, headers=header) as req:
                        pass

        logging.info('Upscale request for message_id [{}] and number [{}] successfully sent!'.format(message_id, number))
