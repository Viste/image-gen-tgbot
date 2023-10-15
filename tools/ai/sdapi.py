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
        self.output_format = "jpg"
        self.model = "stable-diffusion-xl-v1-0"
        self.negatives = """
        (((deformed))), blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), fused fingers, messy drawing, broken legs
        censor, censored, censor_bar, multiple breasts, (mutated hands and fingers:1.5), (long body :1.3), (mutation, poorly drawn :1.2), black-white, bad anatomy, liquid body,
        liquid tongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy, bad proportions,
        bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts, heavy breasts,
        missing breasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf, disappearing legs,
        fused ears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, old photo, low res, black and white, black and white filter, colorless,
        (((deformed))), blurry, bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), fused fingers, messy drawing, broken
        legs censor, censored, censor_bar, multiple breasts, (mutated hands and fingers:1.5), (long body :1.3), (mutation, poorly drawn :1.2), black-white, bad anatomy,
        liquid body, liquid tongue, disfigured, malformed, mutated, anatomical nonsense, text font ui, error, malformed hands, long neck, blurred, lowers, low res, bad anatomy,
        bad proportions, bad shadow, uncoordinated body, unnatural body, fused breasts, bad breasts, huge breasts, poorly drawn breasts, extra breasts, liquid breasts,
        heavy breasts, missing breasts, huge haunch, huge thighs, huge calf, bad hands, fused hand, missing hand, disappearing arms, disappearing thigh, disappearing calf,
        disappearing legs, fused ears, bad ears, poorly drawn ears, extra ears, liquid ears, heavy ears, missing ears, old photo, low res, black and white, black and white filter,
        colorless,(nsfw, naked:1.4)
        """
        self.headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "authorization": "Bearer " + str(self.key)
            }
        self.data = {
            "model": self.model,
            "steps": self.steps,
            "output_format": self.output_format,
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
            "negative_prompt": self.negatives,
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
