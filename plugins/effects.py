# plugins/effects.py
from pyrogram import Client, filters
from pyrogram.types import Message
from database.mongo import db
from config import Config

@Client.on_message(filters.command("bass") & filters.private)
async def bass_cmd(client, message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user.get("is_approved") and user_id != Config.OWNER_ID:
        return await message.reply_text("⛔ Access restricted.")
        
    try:
        value = int(message.command[1])
        await db.update_effect(user_id, "bass", value)
        await message.reply_text(f"🎛️ Bass set to **{value}**")
    except:
        await message.reply_text("Usage: `/bass <0-100>`")
