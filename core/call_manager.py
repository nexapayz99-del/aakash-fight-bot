# core/call_manager.py
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import logging

logger = logging.getLogger(__name__)

class CallManager:
    def __init__(self):
        self.calls = {}

    async def start_call(self, user_id, client, chat_id, fifo_path):
        try:
            if user_id not in self.calls:
                self.calls[user_id] = PyTgCalls(client)
                await self.calls[user_id].start()
            await self.calls[user_id].play(chat_id, MediaStream(fifo_path))
            return True
        except Exception as e:
            logger.error(f"[Call] Failed: {e}")
            return False

    async def stop_call(self, user_id, chat_id):
        if user_id in self.calls:
            try: await self.calls[user_id].leave_call(chat_id)
            except Exception as e: logger.error(f"[Call] Error leaving: {e}")

call_manager = CallManager()