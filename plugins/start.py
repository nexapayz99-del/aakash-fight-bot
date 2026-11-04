# plugins/start.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.mongo import db
from config import Config

RESTRICTED_TEXT = """
⛔ <b>ACCESS RESTRICTED</b>
━━━━━━━━━━━━━━━━━━━━
Hello {username},
You need approval to use this bot.
📩 <b>Request forwarded to admins.</b>
━━━━━━━━━━━━━━━━━━━━
You will be notified once approved.
"""

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 Audio Controls", callback_data="menu_audio"), InlineKeyboardButton("🎛️ Audio Effects", callback_data="menu_effects")],
        [InlineKeyboardButton("📱 My Accounts", callback_data="menu_accounts"), InlineKeyboardButton("📊 Utility", callback_data="menu_utility")]
    ])

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if user.get("is_banned"):
        return await message.reply_text("🚫 You are banned from using this bot.")
        
    if not user.get("is_approved") and user_id != Config.OWNER_ID:
        await message.reply_text(
            RESTRICTED_TEXT.format(username=message.from_user.mention),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔒 Pending Approval", callback_data="noop")]])
        )
        
        # Send to owner
        try:
            await client.send_message(
                Config.OWNER_ID,
                f"🔔 <b>New Access Request</b>\n\n"
                f"👤 Name: {message.from_user.first_name}\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"🔗 Username: @{message.from_user.username}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Approve Access", callback_data=f"approve_{user_id}")],
                    [InlineKeyboardButton("🚫 Ban User", callback_data=f"ban_{user_id}")]
                ])
            )
        except Exception as e:
            print(f"Failed to send to owner: {e}")
        return

    # Normal Start
    await message.reply_text(
        f"✨ <b>Welcome to Audio Forwarder</b> ✨\n\n"
        f"👋 Hello, {message.from_user.first_name}!\n"
        f"Use the buttons below to control your audio pipeline.",
        reply_markup=main_menu()
    )

@Client.on_callback_query(filters.regex("^menu_"))
async def menu_callbacks(client, callback_query: CallbackQuery):
    data = callback_query.data
    
    if data == "menu_audio":
        text = "🎵 <b>Audio Controls</b>\n\n/record - Start recording\n/join - Forward to chat\n/leaveall - Stop all"
    elif data == "menu_effects":
        text = "🎛️ <b>Audio Effects</b>\n\n/bass <0-100>\n/treble <0-100>\n/echo <delay/decay>\n/reset - Reset all effects"
    elif data == "menu_accounts":
        text = "📱 <b>My Accounts</b>\n\n(Account management UI goes here)"
    elif data == "menu_utility":
        text = "📊 <b>Utility</b>\n\n/ping - Check bot latency\n/id - Get chat ID"
    else:
        return await callback_query.answer("Coming soon!", show_alert=True)
        
    await callback_query.message.edit_text(text, reply_markup=main_menu())

@Client.on_callback_query(filters.regex("^noop$"))
async def noop(client, callback_query):
    await callback_query.answer("Waiting for admin approval...", show_alert=True)
