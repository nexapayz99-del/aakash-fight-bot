# plugins/audio.py
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from database.mongo import db
from config import Config
from core.call_manager import call_manager
from core.audio_dsp import AudioDSP

async def show_progress_bar(msg: Message, action_name: str, total_steps: int = 5):
    for step in range(1, total_steps + 1):
        percent = int((step / total_steps) * 100)
        bar = f"[{'█' * step}{'░' * (total_steps - step)}] {percent}%"
        try:
            await msg.edit_text(f"⚙️ <b>{action_name}...</b>\n━━━━━━━━━━━━━━━━━━━━\n{bar}")
        except: pass
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
    await msg.edit_text(f"✅ <b>Connected!</b>\n🎵 Target: <code>{chat_id}</code>")

@Client.on_message(filters.command("leaveall") & filters.private)
async def leave_all(client, message: Message):
    msg = await message.reply_text("Disconnecting...")
    await show_progress_bar(msg, "Disconnecting", 5)
    await msg.edit_text("✅ <b>All chats disconnected successfully!</b>")

@Client.on_callback_query(filters.regex(r"^audio_"))
async def audio_actions(client, query: CallbackQuery):
    await query.answer()
    action = query.data.split("_", 1)[1]
    user_id = query.from_user.id
    user = await db.get_user(user_id)

    if action == "disc":
        await query.message.edit_text("🛑 **Disconnected all streams.**")
    elif action == "src":
        try:
            # FIXED: use client.ask()
            response = await client.ask(
                query.message.chat.id,
                "🎯 <b>Send the Chat ID (Source):</b>\n<i>e.g., -100123456</i>\n\nType /cancel to abort.",
                timeout=60
            )
            if response.text.strip().lower() == "/cancel":
                return await response.reply_text("❌ Cancelled.")
            chat_id = int(response.text.strip())
            await db.users.update_one({"_id": user_id}, {"$set": {"record_group_id": chat_id}})
            await response.reply_text(f"✅ Source Chat set to <code>{chat_id}</code>")
        except (asyncio.TimeoutError, ValueError):
            await query.message.reply_text("❌ Invalid input or timeout.")
    elif action == "join":
        if not user.get("record_group_id"):
            return await query.message.reply_text("❌ Please set a Source Chat first!")
        msg = await query.message.edit_text("Initializing...")
        await show_progress_bar(msg, "Connecting Audio Stream", 5)
        accounts = await db.get_accounts(user_id)
        if not accounts:
            return await msg.edit_text("❌ No userbot accounts found! Go to My Accounts to login.")
        dsp = AudioDSP(user_id)
        await dsp.setup_sink()
        await dsp.start_ffmpeg(user["effects"])
        await msg.edit_text(f"✅ **Audio Stream Connected!**\n🎵 Target: <code>{user['record_group_id']}</code>")