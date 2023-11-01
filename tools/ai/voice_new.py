import logging
from elevenlabslib import *

from tools.utils import config

logger = logging.getLogger(__name__)


class ELAI:
    def __init__(self):
        super().__init__()
        self.user = ElevenLabsUser(config.el_key)
        self.model = "eleven_monolingual_v2"
        self.voice = self.user.get_voices_by_name("NASTYA")[0]

    async def send2api(self, text, uid):
        content = self.voice.generate_audio_v2(text, GenerationOptions(model="eleven_multilingual_v2", stability=0.94, style=0.5, similarity_boost=0.75))
        save_audio_bytes(content[0], f'{str(uid)}.mp3', outputFormat="mp3")
        with open(f'{str(uid)}.mp3', 'wb') as f:
            f.write(content)
        return f'{str(uid)}.mp3'
