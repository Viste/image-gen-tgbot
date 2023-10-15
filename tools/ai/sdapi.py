import logging
import aiohttp

from tools.utils import config

logger = logging.getLogger(__name__)


class SDAI:
    def __init__(self):
        super().__init__()
        self.key = config.sd_key
        self.url = config.sd_url
        self.samples = 1
        self.width = 768
        self.height = 768
        self.steps = 50
        self.guidance_scale = 7.5
        self.scheduler = "euler"
        self.model = "stable-diffusion-xl-v1-0"
        self.negatives = "(((deformed))), blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), fused fingers, messy drawing"
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "authorization": "Bearer " + str(self.key)
            }
        self.data = {
            "model": self.model,
            "steps": self.steps,
            "width": self.width,
            "height": self.height,
            "guidance_scale": self.guidance_scale,
            }

    async def _send_req(self, url, data):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as resp:
                return await resp.json()

    async def s2sdapi(self, prompt):
        data = self.data.copy()
        data.update({
            "prompt": prompt,
            })
        return await self._send_req(self.url, data)

    async def neda_gen(self, prompt):
        data = self.data.copy()
        data.update({
            "prompt": prompt,
            "negative_prompt": self.negatives,
            })
        response = await self._send_req(self.url, data)
        return response["output"][0]
