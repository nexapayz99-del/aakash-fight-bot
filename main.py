# main.py
import pyromod.listen  # MUST be first — activates client.ask() / client.listen()
import logging
from pyrogram import Client
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

app = Client(
    "AakashFightBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins")
)

if __name__ == "__main__":
    print("Bot Started...")
    app.run()