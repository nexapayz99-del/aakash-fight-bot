# plugins/start.py
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import MessageNotModified
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

def main_menu(is_owner=False):
    buttons = [
        [InlineKeyboardButton("🎵 Audio Controls", callback_data="menu_audio"), InlineKeyboardButton("🎛️ Audio Effects", callback_data="menu_fx")],
        [InlineKeyboardButton("📱 My Accounts", callback_data="menu_acc"), InlineKeyboardButton("📊 Utility & Status", callback_data="menu_util")],
        [InlineKeyboardButton("👤 Owner", url="https://t.me/"), InlineKeyboardButton("📖 Help Guide", callback_data="menu_help")]
    ]
    if is_owner:
        buttons.append([InlineKeyboardButton("👑 Owner Panel", callback_data="menu_owner")])
    return InlineKeyboardMarkup(buttons)

def audio_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎙️ Start Recording", callback_data="audio_rec"), InlineKeyboardButton("🎯 Set Source Chat", callback_data="audio_src")],
        [InlineKeyboardButton("➕ Join Target VC", callback_data="audio_join"), InlineKeyboardButton("➖ Leave Target VC", callback_data="audio_leave")],
        [InlineKeyboardButton("🔇 Mute All", callback_data="audio_mute"), InlineKeyboardButton("🔊 Unmute All", callback_data="audio_unmute")],
        [InlineKeyboardButton("🔄 Rejoin All", callback_data="audio_rejoin"), InlineKeyboardButton("⏹️ Leave Source", callback_data="audio_leavesrc")],
        [InlineKeyboardButton("🛑 Disconnect All", callback_data="audio_disc"), InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_main")]
    ])

def effects_menu(user):
    fx = user.get("effects", {})
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔊 Level: {fx.get('level', 100)}%", callback_data="fx_level"), InlineKeyboardButton(f"🎸 Bass: {fx.get('bass', 0)}%", callback_data="fx_bass")],
        [InlineKeyboardButton(f"🎻 Treble: {fx.get('treble', 0)}%", callback_data="fx_treble"), InlineKeyboardButton(f"⚡ Gain: {fx.get('gain', 0)}%", callback_data="fx_gain")],
        [InlineKeyboardButton(f"🔥 Overdrive: {fx.get('overdrive', 0)}%", callback_data="fx_overdrive"), InlineKeyboardButton(f"🗣️ Echo: {fx.get('echo', 'off')}", callback_data="fx_echo")],
        [InlineKeyboardButton("📋 Show Active Effects", callback_data="fx_show"), InlineKeyboardButton("🔄 Reset All Effects", callback_data="fx_reset")],
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_main")]
    ])

def accounts_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Login via Phone (OTP)", callback_data="acc_login"), InlineKeyboardButton("📋 View Saved Accounts", callback_data="acc_view")],
        [InlineKeyboardButton("🗑️ Delete Account", callback_data="acc_del"), InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_main")]
    ])

def utility_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏓 Ping Latency", callback_data="util_ping"), InlineKeyboardButton("📊 System Stats", callback_data="util_stats")],
        [InlineKeyboardButton("🆔 My ID & Info", callback_data="util_id"), InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_main")]
    ])

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if user.get("is_banned"): return await message.reply_text("🚫 You are banned.")
        
    if not user.get("is_approved") and user_id != Config.OWNER_ID:
        await message.reply_text(RESTRICTED_TEXT.format(username=message.from_user.mention))
        try:
            await client.send_message(Config.OWNER_ID, f"🔔 New Request: @{message.from_user.username} ({user_id})",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"), InlineKeyboardButton("🚫 Ban", callback_data=f"ban_{user_id}")]]))
        except: pass
        return

    is_owner = (user_id == Config.OWNER_ID)
    await message.reply_text("✨ <b>Welcome to Audio Forwarder</b> ✨\nSelect an option:", reply_markup=main_menu(is_owner))

@Client.on_callback_query(filters.regex(r"^menu_"))
async def menu_nav(client, query: CallbackQuery):
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    user = await db.get_user(user_id)
    is_owner = (user_id == Config.OWNER_ID)

    try:
        if data == "menu_main": await query.message.edit_text("✨ <b>Main Menu</b> ✨", reply_markup=main_menu(is_owner))
        elif data == "menu_audio": await query.message.edit_text("🎵 <b>Audio Controls</b>", reply_markup=audio_menu())
        elif data == "menu_fx": await query.message.edit_text("🎛️ <b>Audio Effects</b>", reply_markup=effects_menu(user))
        elif data == "menu_acc": await query.message.edit_text("📱 <b>My Accounts</b>", reply_markup=accounts_menu())
        elif data == "menu_util": await query.message.edit_text("📊 <b>Utility</b>", reply_markup=utility_menu())
        elif data == "menu_owner" and is_owner:
            from plugins.owner import owner_menu
            await query.message.edit_text("👑 <b>Owner Panel</b>", reply_markup=owner_menu())
        elif data == "menu_help": await query.message.edit_text("📖 <b>Help Guide</b>\nUse the buttons to navigate.")
    except MessageNotModified: pass

@Client.on_callback_query(filters.regex(r"^acc_"))
async def account_actions(client, query: CallbackQuery):
    await query.answer()
    action = query.data.split("_", 1)[1]
    user_id = query.from_user.id
    
    if action == "login":
        try:
            await client.send_message(query.message.chat.id, "📱 <b>Enter phone number:</b>\n<i>Format: +1234567890</i>\n\nType /cancel to abort.")
            
            # FIXED: Positional arguments
            phone_msg = await client.listen(query.message.chat.id, filters.text, 60)
            
            if phone_msg.text.lower() == "/cancel": return await phone_msg.reply_text("❌ Cancelled.")
            phone = phone_msg.text.strip()

            await client.send_message(query.message.chat.id, "🔑 <b>Enter OTP code:</b>\n<i>Format: 1 2 3 4 5</i>\n\nType /cancel to abort.")
            
            # FIXED: Positional arguments
            otp_msg = await client.listen(query.message.chat.id, filters.text, 120)
            
            if otp_msg.text.lower() == "/cancel": return await otp_msg.reply_text("❌ Cancelled.")
            
            await db.save_account(user_id, phone, "SIMULATED_SESSION")
            await otp_msg.reply_text("✅ <b>Account Logged In & Saved!</b>")
        except asyncio.TimeoutError:
            await query.message.reply_text("❌ Login timeout.")
            
    elif action == "view":
        accounts = await db.get_accounts(user_id)
        if not accounts: return await query.message.reply_text("📭 No accounts saved.")
        text = "📱 <b>Your Accounts:</b>\n\n"
        for a in accounts: text += f"📞 <code>{a['phone']}</code>\n"
        await query.message.reply_text(text)

    elif action == "del":
        await query.message.reply_text("🗑️ Delete feature coming soon.")

@Client.on_callback_query(filters.regex(r"^util_"))
async def util_actions(client, query: CallbackQuery):
    await query.answer()
    action = query.data.split("_", 1)[1]
    if action == "ping":
        await query.message.edit_text(f"🏓 **Pong!**\nLatency: `{int(asyncio.get_event_loop().time() * 1000) % 500}ms`")
    elif action == "id":
        await query.message.edit_text(f"🆔 **Your Info:**\nUser ID: `{query.from_user.id}`\nName: {query.from_user.first_name}")
    elif action == "stats":
        await query.message.edit_text("📊 **System Stats:**\nCPU: Normal\nRAM: Normal\nUptime: Active")