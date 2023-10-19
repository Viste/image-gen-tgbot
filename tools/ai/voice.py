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
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": str(self.key)
            }
        self.data = {
            "model": self.model,
            }

    async def _send_req(self, url, data):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as resp:
                logger.info("SEND REQUEST LOGGER %s", resp)
                return await resp.read()

    async def send2api(self, text, uid):
        data = self.data.copy()
        data.update({
            "text": text,
            "voice_settings": {
                "stability": 1,
                "similarity_boost": 0.9,
                "style": 0.6,
                "use_speaker_boost": True
                }
            })
        content = await self._send_req(self.url, data)
        with open(f'{str(uid)}.mp3', 'wb') as f:
            f.write(content)
        return f'{str(uid)}.mp3'
