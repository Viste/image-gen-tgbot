import logging
import aiohttp

from tools.utils import config

logger = logging.getLogger(__name__)


class ELAI:
    def __init__(self):
        super().__init__()
        self.key = config.el_key
        self.url = "https://api.elevenlabs.io/v1/text-to-speech/dWvQRPctX7BT3AMBjjdX"
        self.model = "eleven_monolingual_v2"
        self.headers = {
            "accept": "audio/mpeg",
            "Content-Type": "application/json",
            "authorization": "Bearer " + str(self.key)
            }
        self.data = {
            "model": self.model,
            }

    async def _send_req(self, url, data):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as resp:
                logger.info(resp)
                return await resp.json()

    async def send2api(self, text):
        data = self.data.copy()
        data.update({
            "text": text,
            })
        return await self._send_req(self.url, data)
