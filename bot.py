from pyrogram import Client
from config import config
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class Bot(Client):
    def __init__(self):
        super().__init__(
            "subtitle_bot",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            plugins=dict(root="handlers")
        )
    
    async def start(self):
        await super().start()
        logger.info("Bot started")
    
    async def stop(self, *args):
        await super().stop()
        logger.info("Bot stopped")

if __name__ == "__main__":
    Bot().run()
