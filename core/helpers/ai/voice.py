import logging
from elevenlabslib import *

from tools.utils import config

logger = logging.getLogger(__name__)


class ELAI:
    def __init__(self):
        super().__init__()
        self.user = ElevenLabsUser(config.el_key)
        self.model = "eleven_monolingual_v2"
        self.voice = self.user.get_voices_by_name("NastyaBot")[0]

    def send2api(self, text, uid):
        content = self.voice.generate_audio_v2(text, GenerationOptions(model="eleven_multilingual_v2",
                                                                       stability=0.9, style=0.4,
                                                                       similarity_boost=0.7))
        save_audio_bytes(content[0], f'{str(uid)}.mp3', outputFormat="mp3")
        return f'{str(uid)}.mp3'
