import logging

import aiohttp

from tools.utils import config

logger = logging.getLogger(__name__)


class StableDiffAI:
    def __init__(self):
        super().__init__()
        self.key = config.sd_api_key
        self.url = config.sd_api_url
        self.video_url = "https://stablediffusionapi.com/api/v5/text2video"
        self.fetch_url = "https://stablediffusionapi.com/api/v4/dreambooth/fetch"
        self.samples = 1
        self.width = 768
        self.height = 768
        self.steps = 50
        self.guidance_scale = 7.5
        self.video_length = 10
        self.video_negative = "Low Quality"
        self.scheduler = "DDIMInverseScheduler"
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
            "Content-Type": "application/json"
            }
        self.data = {
            "key": self.key,
            "samples": self.samples,
            "width": self.width,
            "height": self.height,
            "guidance_scale": self.guidance_scale,
            "num_inference_steps": self.steps,
            }

    async def _send_request(self, url, data):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as resp:
                return await resp.json()

    async def send2sdapi(self, prompt):
        data = self.data.copy()
        data.update({
            "model_id": "realistic-vision-v13",
            "prompt": prompt,
            "negative_prompt": self.negatives,
            "multi_lingual": "yes",
        })
        return await self._send_request(self.url, data)

    async def gen_ned_img(self, prompt):
        data = self.data.copy()
        data.update({
            "prompt": prompt,
            "negative_prompt": self.negatives,
        })
        response = await self._send_request(self.url, data)
        return response["output"][0]

    async def send2sd_video(self, prompt):
        data = {
            "key": self.key,
            "prompt": prompt,
            "negative_prompt": self.video_negative,
            "scheduler": self.scheduler,
            "seconds": self.video_length,
        }
        return await self._send_request(self.video_url, data)

    async def get_queued(self, img_id: int):
        payload = {
            "key": self.key,
            "request_id": img_id
            }
        async with aiohttp.ClientSession() as session:
            async with session.post(self.fetch_url, headers=self.headers, data=payload) as resp:
                return await resp.json()
