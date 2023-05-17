import logging

from dateutil.parser import parse

from artint.mj.receiver import Receiver
from artint.mj.sender import Sender
from artint.mj.upscaler import Upscaler

logger = logging.getLogger("__name__")


class ImageGenerator:
    def __init__(self, params, index):
        self.sender = Sender(params, index, 0)
        self.receiver = Receiver(params, index)
        self.upscaler = Upscaler(params, index)

    async def generate_image(self, prompt):
        # Send the prompt to Midjourney
        self.sender.send(prompt)

        # Wait for the result from Midjourney
        while True:
            # await asyncio.sleep(5)  # Wait for 5 seconds before checking for new messages
            self.receiver.collecting_results()
            if not self.receiver.df.empty:
                latest_image = self.receiver.df.iloc[-1]
                if parse(latest_image["timestamp"]) > self.receiver.latest_image_timestamp:
                    break

        # Extract the required part from the URL
        url = latest_image["url"]
        message_id = latest_image.name
        paperclip_part = url.split("/")[-1]

        # Pass the extracted part to the upscaler
        number = 3  # Choose the number of the image to upscale (1, 2, 3, or 4)
        self.upscaler.send(message_id, number, paperclip_part)

        # Wait for the scaled image URL
        while True:
            await asyncio.sleep(5)  # Wait for 5 seconds before checking for new messages
            self.receiver.collecting_results()
            scaled_image = self.receiver.df.loc[message_id]
            if scaled_image["is_downloaded"]:
                scaled_url = scaled_image["url"]
                break

        return scaled_url
