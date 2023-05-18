import asyncio
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
            await asyncio.sleep(120)  # Wait for 180 seconds before checking for new messages
            logging.info("We are in loop")
            self.receiver.collecting_results()
            logging.info("PRINTING loc %s\n", self.receiver.df.loc)
            logging.info("PRINTING iat %s\n", self.receiver.df.iat)
            logging.info("results collected")
            if not self.receiver.df.empty:
                latest_image = self.receiver.df.iloc[-1]
                print("PRINTING: %s", self.receiver.df.loc)
                if "timestamp" in self.receiver.df.columns and parse(latest_image["timestamp"]) > self.receiver.latest_image_timestamp:
                    print("Image received:", latest_image)
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
            await asyncio.sleep(240)  # Wait for 5 seconds before checking for new messages
            logging.info("In upscale loop")
            self.receiver.collecting_results()
            logging.info("Result received")
            scaled_image = self.receiver.df.loc[message_id]
            if scaled_image["is_downloaded"]:
                print("Scaled image received:", scaled_image)
                scaled_url = scaled_image["url"]
                break

        return scaled_url
