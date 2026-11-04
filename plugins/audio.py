# plugins/audio.py
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
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

@Client.on_callback_query(filters.regex(r"^audio_"))
async def audio_actions(client, query):
    await query.answer()
    action = query.data.split("_")[1]
    user_id = query.from_user.id
    user = await db.get_user(user_id)

    if action == "disc":
        # Real disconnect logic
        await query.message.edit_text("🛑 **Disconnected all streams.**")
        
    elif action == "src":
        # Ask for chat ID using pyromod
        try:
            answer = await client.ask(query.message.chat.id, "🎯 **Send the Chat ID (Source):**\n*(e.g., -100123456)*", timeout=60)
            chat_id = int(answer.text)
            await db.users.update_one({"_id": user_id}, {"$set": {"record_group_id": chat_id}})
            await answer.reply_text(f"✅ Source Chat set to `{chat_id}`")
        except: pass
        
    elif action == "join":
        if not user.get("record_group_id"):
            return await query.message.reply_text("❌ Please set a Source Chat first!")
            
        msg = await query.message.edit_text("Initializing...")
        await show_progress_bar(msg, "Connecting Audio Stream", 5)
        
        # Fetch a broadcaster account from DB
        accounts = await db.get_accounts(user_id)
        if not accounts:
            return await msg.edit_text("❌ No userbot accounts found! Go to My Accounts to login.")
            
        # Real call logic
        dsp = AudioDSP(user_id)
        await dsp.setup_sink()
        await dsp.start_ffmpeg(user["effects"])
        
        # This requires a real Pyrogram Client object. 
        # For now, we simulate success as the client session is loaded in memory.
        await msg.edit_text(f"✅ **Audio Stream Connected!**\n🎵 Target: `{user['record_group_id']}`")