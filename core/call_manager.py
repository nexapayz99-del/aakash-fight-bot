# core/call_manager.py
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
import logging

logger = logging.getLogger(__name__)

class CallManager:
    def __init__(self):
        self.calls = {}  # {user_id: PyTgCalls}

    async def start_call(self, user_id, client, chat_id, fifo_path):
        try:
            if user_id not in self.calls:
                self.calls[user_id] = PyTgCalls(client)
                await self.calls[user_id].start()

            # v2+ uses play() with MediaStream
            await self.calls[user_id].play(
                chat_id,
                MediaStream(fifo_path)
            )
            logger.info(f"[Call] User {user_id} joined {chat_id}")
            return True
        except Exception as e:
            logger.error(f"[Call] Failed to join {chat_id}: {e}")
            return False

    async def stop_call(self, user_id, chat_id):
        if user_id in self.calls:
            try:
                await self.calls[user_id].leave_call(chat_id)
                logger.info(f"[Call] User {user_id} left {chat_id}")
            except Exception as e:
                logger.error(f"[Call] Error leaving {chat_id}: {e}")

call_manager = CallManager()
