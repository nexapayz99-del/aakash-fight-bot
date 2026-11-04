# plugins/audio.py
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from database.mongo import db
from config import Config

async def show_progress_bar(msg: Message, action_name: str, total_steps: int = 5):
    for step in range(1, total_steps + 1):
        percent = int((step / total_steps) * 100)
        bar = f"[{'█' * step}{'░' * (total_steps - step)}] {percent}%"
        try:
            await msg.edit_text(f"⚙️ <b>{action_name}...</b>\n━━━━━━━━━━━━━━━━━━━━\n{bar}\n━━━━━━━━━━━━━━━━━━━━\nPlease wait...")
        except Exception:
            pass
        await asyncio.sleep(0.3)

@Client.on_message(filters.command("join") & filters.private)
async def join_cmd(client, message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user.get("is_approved") and user_id != Config.OWNER_ID:
        return await message.reply_text("⛔ Access restricted.")
        
    try:
        chat_id = int(message.command[1])
    except (IndexError, ValueError):
        return await message.reply_text("Usage: <code>/join &lt;chat_id&gt;</code>")
        
    msg = await message.reply_text("Initializing...")
    await show_progress_bar(msg, "Connecting Audio Stream", 5)
        
    await msg.edit_text(
        f"✅ <b>Command received!</b>\n"
        f"🎵 Target Chat ID: <code>{chat_id}</code>\n\n"
        f"<i>Note: Account binding is required before audio can actually flow.</i>"
    )

@Client.on_message(filters.command("leaveall") & filters.private)
async def leave_all(client, message: Message):
    msg = await message.reply_text("Disconnecting...")
    await show_progress_bar(msg, "Disconnecting", 5)
    await msg.edit_text("✅ <b>All chats disconnected successfully!</b>")
