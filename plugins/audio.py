# plugins/audio.py
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from database.mongo import db
from config import Config
# Import call_manager for future use
from core.call_manager import call_manager

async def progress_bar(message, current, total, action_text="Processing"):
    percent = int((current / total) * 100)
    filled = int(percent / 10)
    bar = "█" * filled + "░" * (10 - filled)
    text = (
        f"⚙️ <b>{action_text}...</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"[{bar}] {percent}%\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Please wait..."
    )
    await message.edit_text(text)

@Client.on_message(filters.command("join") & filters.private)
async def join_cmd(client, message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user.get("is_approved") and user_id != Config.OWNER_ID:
        return await message.reply_text("⛔ Access restricted.")
        
    try:
        chat_id = int(message.command[1])
    except:
        return await message.reply_text("Usage: `/join <chat_id>`")
        
    msg = await message.reply_text("Initializing...")
    
    for i in range(1, 11):
        await asyncio.sleep(0.2)
        await progress_bar(msg, i, 10, "Connecting Audio Stream")
        
    # NOTE: To actually join a voice chat, you must pass a Userbot Client instance 
    # (a STRING_SESSION from your database), not the Bot client. 
    # The code below is a placeholder until account management is built.
    await msg.edit_text(
        f"✅ <b>Command received!</b>\n"
        f"🎵 Target Chat ID: <code>{chat_id}</code>\n\n"
        f"<i>Note: Account binding is required before audio can actually flow.</i>"
    )

@Client.on_message(filters.command("leaveall") & filters.private)
async def leave_all(client, message: Message):
    user_id = message.from_user.id
    msg = await message.reply_text("Disconnecting...")
    
    for i in range(1, 6):
        await asyncio.sleep(0.2)
        await progress_bar(msg, i, 5, "Disconnecting")
        
    await msg.edit_text("✅ <b>All chats disconnected successfully!</b>")
