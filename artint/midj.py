import asyncio
import logging
import re

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
            try:
                await asyncio.sleep(120)  # Wait for 180 seconds before checking for new messages
                logging.info("We are in loop")
                await self.receiver.collecting_results()
                logging.info("results collected")
                if not self.receiver.df.empty:
                    latest_image = self.receiver.df.iloc[-1]
                    logging.info(f"Latest image timestamp: {latest_image['timestamp']}")
                    logging.info(f"Receiver latest image timestamp: {self.receiver.latest_image_timestamp}")
                    if latest_image["timestamp"] >= self.receiver.latest_image_timestamp:
                        logging.info("Breaking the loop")
                        logging.info("Container content: %s", latest_image)
                        break
                    else:
                        logging.info("No new image found. Continuing the loop.")
                else:
                    logging.info("DataFrame is empty. Continuing the loop.")
            except Exception as e:
                logging.error(f"An error occurred: {e}")
                logging.info("An error occurred. Continuing the loop.")  # Add a small delay before the next iteration

        # Extract the required part from the URL
        # Extract the required part from the URL
        url = latest_image["url"]
        message_id = latest_image.name
        filename = latest_image["filename"]

        # Extract the UUID part from the filename
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        uuid_match = re.search(uuid_pattern, filename)
        if uuid_match:
            paperclip_part = uuid_match.group(0)
        else:
            logging.error("UUID not found in the filename")
            return None

        number = 3  # Choose the number of the image to upscale (1, 2, 3, or 4)
        logging.info("Sending upscale request")
        await self.upscaler.send(message_id, number, paperclip_part)
        logging.info("Upscale request sent")

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
