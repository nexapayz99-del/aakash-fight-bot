# plugins/owner.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from database.mongo import db
from config import Config

async def _is_approval(_, __, query: CallbackQuery):
    return query.data and (query.data.startswith("approve_") or query.data.startswith("ban_"))

approval_filter = filters.create(_is_approval)

# group=1 means it runs AFTER the group=0 menu_router, avoiding collisions
@Client.on_callback_query(approval_filter, group=1)
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
            try:
                await client.send_message(target_id, "✅ <b>Your access has been approved!</b>\nSend /start to begin.")
            except Exception:
                pass
        elif action == "ban":
            await db.users.update_one({"_id": target_id}, {"$set": {"is_banned": True}}, upsert=True)
            await query.message.edit_text(f"🚫 User {target_id} Banned!")
    except Exception as e:
        print(f"Approval Error: {e}")
