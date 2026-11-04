# plugins/owner.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from database.mongo import db
from config import Config
import os, sys

@Client.on_callback_query(filters.regex(r"^(approve|ban)_(\d+)$"))
async def handle_approval(client, query: CallbackQuery):
    if query.from_user.id != Config.OWNER_ID:
        return await query.answer("❌ Not authorized", show_alert=True)
    await query.answer()
    action, target_id = query.data.split("_")
    target_id = int(target_id)
    
    try:
        if action == "approve":
            await db.approve_user(target_id)
            await query.message.edit_text(f"✅ User {target_id} Approved!")
            try: await client.send_message(target_id, "✅ <b>Your access has been approved!</b>\nSend /start to begin.")
            except: pass
        elif action == "ban":
            await db.users.update_one({"_id": target_id}, {"$set": {"is_banned": True}}, upsert=True)
            await query.message.edit_text(f"🚫 User {target_id} Banned!")
    except Exception as e:
        print(f"[Approval] {e}")

@Client.on_callback_query(filters.regex(r"^own_"))
async def owner_panel_actions(client, query: CallbackQuery):
    if query.from_user.id != Config.OWNER_ID:
        return await query.answer("❌ Not authorized", show_alert=True)
    await query.answer()
    
    action = query.data.split("_")[1]
    
    if action == "users":
        users = await db.users.find({"is_approved": True}).to_list(100)
        text = f"📋 **Total Approved Users: {len(users)}**\n\n"
        for u in users[:10]: # Show first 10
            text += f"🆔 <code>{u['_id']}</code>\n"
        if len(users) > 10: text += "\n*(Only showing first 10)*"
        await query.message.edit_text(text)
        
    elif action == "restart":
        await query.message.edit_text("🔄 **Restarting Bot...**")
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    else:
        # Placeholder for prompt-based owner actions (Ban/Unban)
        await query.message.reply_text(f"⚙️ Action `{action}` triggered. (Requires user ID prompt implementation)")