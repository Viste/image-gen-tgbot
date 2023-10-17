import logging
from elevenlabs import Voice, VoiceSettings, generate

from tools.utils import config

logger = logging.getLogger(__name__)


class ELAI:
    def __init__(self):
        super().__init__()
        self.key = config.el_key

    async def gen_voice(self, text):
        txt = generate(
            api_key=self.key,
            text=text,
            voice="NASTYA",
            model="eleven_multilingual_v2"
            )
        return txt
