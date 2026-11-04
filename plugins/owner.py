# plugins/owner.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from database.mongo import db
from config import Config

@Client.on_callback_query(filters.regex(r"^(approve|ban)_(\d+)$"))
async def handle_approval(client, callback_query: CallbackQuery):
    if callback_query.from_user.id != Config.OWNER_ID:
        return await callback_query.answer("❌ Not authorized", show_alert=True)
        
    action, user_id = callback_query.data.split("_")
    user_id = int(user_id)
    
    if action == "approve":
        await db.approve_user(user_id)
        await callback_query.edit_message_text(f"✅ User {user_id} Approved!")
        try:
            await client.send_message(user_id, "✅ <b>Your access has been approved!</b>\nSend /start to begin.")
        except:
            pass
            
    elif action == "ban":
        await db.users.update_one({"_id": user_id}, {"$set": {"is_banned": True}}, upsert=True)
        await callback_query.edit_message_text(f"🚫 User {user_id} Banned!")
