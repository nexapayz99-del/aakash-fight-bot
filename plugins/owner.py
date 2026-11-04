# plugins/owner.py
import asyncio, os, sys
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.mongo import db
from config import Config

def owner_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve User", callback_data="own_approve"), InlineKeyboardButton("❌ Remove Access", callback_data="own_remove")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="own_ban"), InlineKeyboardButton("🟢 Unban User", callback_data="own_unban")],
        [InlineKeyboardButton("📋 View All DB Users", callback_data="own_users"), InlineKeyboardButton("🔄 Restart Bot", callback_data="own_restart")],
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_main")]
    ])

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
        print(f"[handle_approval] {e}")

@Client.on_callback_query(filters.regex(r"^own_"))
async def owner_panel_actions(client, query: CallbackQuery):
    if query.from_user.id != Config.OWNER_ID:
        return await query.answer("❌ Not authorized", show_alert=True)
    await query.answer()
    action = query.data.split("_", 1)[1]

    if action in ("approve", "remove", "ban", "unban"):
        try:
            prompt = await client.send_message(query.message.chat.id, f"👑 <b>Send the User ID to {action}:</b>\n\nType /cancel to abort.")
            
            # FIXED: Positional arguments
            response = await client.listen(query.message.chat.id, filters.text, 60)
            
            if response.text.lower() == "/cancel": return await response.reply_text("❌ Cancelled.")
            target_id = int(response.text.strip())

            if action == "approve":
                await db.approve_user(target_id)
                await response.reply_text(f"✅ Approved {target_id}")
                try: await client.send_message(target_id, "✅ <b>Approved!</b>")
                except: pass
            elif action == "remove":
                await db.users.update_one({"_id": target_id}, {"$set": {"is_approved": False}}, upsert=True)
                await response.reply_text(f"❌ Removed access for {target_id}")
            elif action == "ban":
                await db.users.update_one({"_id": target_id}, {"$set": {"is_banned": True}}, upsert=True)
                await response.reply_text(f"🚫 Banned {target_id}")
            elif action == "unban":
                await db.users.update_one({"_id": target_id}, {"$set": {"is_banned": False}}, upsert=True)
                await response.reply_text(f"🟢 Unbanned {target_id}")
        except asyncio.TimeoutError:
            await prompt.edit_text("❌ Timeout.")
        except ValueError:
            await prompt.edit_text("❌ Invalid User ID.")
        return

    if action == "users":
        users = await db.users.find({"is_approved": True}).to_list(100)
        text = f"📋 <b>Total Approved Users: {len(users)}</b>\n\n"
        for u in users[:15]: text += f"🆔 <code>{u['_id']}</code>\n"
        if len(users) > 15: text += f"\n<i>Showing 15 of {len(users)}</i>"
        await query.message.edit_text(text)
        return

    if action == "restart":
        await query.message.edit_text("🔄 <b>Restarting Bot...</b>")
        await asyncio.sleep(1)
        os.execl(sys.executable, sys.executable, *sys.argv)