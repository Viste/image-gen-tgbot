import asyncio
import logging

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
        await self.sender.send(prompt)

        # Wait for the result from Midjourney
        while True:
            await asyncio.sleep(120)  # Wait for 180 seconds before checking for new messages
            logging.info("We are in loop")
            await self.receiver.collecting_results()
            logging.info("results collected")
            if not self.receiver.df.empty:
                latest_image = self.receiver.df.iloc[-1]
                if latest_image["timestamp"]:
                    logging.info("img found %s", latest_image)
                    break
                else:
                    logging.info("No new image found. Continuing the loop.")
            else:
                logging.info("DataFrame is empty. Continuing the loop.")

        # Extract the required part from the URL
        url = latest_image["url"]
        message_id = latest_image.name
        paperclip_part = url.split("/")[-1]

        # Pass the extracted part to the upscaler
        number = 3  # Choose the number of the image to upscale (1, 2, 3, or 4)
        await self.upscaler.send(message_id, number, paperclip_part)

        # Wait for the scaled image URL
        while True:
            await asyncio.sleep(240)  # Wait for 5 seconds before checking for new messages
            logging.info("In upscale loop")
            await self.receiver.collecting_results()
            logging.info("Result received")
            scaled_image = self.receiver.df.loc[message_id]
            if scaled_image["is_downloaded"]:
                logging.info("Scaled image received:", scaled_image)
                scaled_url = scaled_image["url"]
                break

        return scaled_url
