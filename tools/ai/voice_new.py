import logging

from tools.utils import config

logger = logging.getLogger(__name__)


class ELAI:
    def __init__(self):
        super().__init__()
        self.user = config.el_key
        self.url = "https://api.elevenlabs.io/v1/text-to-speech/dWvQRPctX7BT3AMBjjdX?optimize_streaming_latency=0"
        self.model = "eleven_monolingual_v2"
        self.voice = self.user.get_voices_by_name("NASTYA")[0]
