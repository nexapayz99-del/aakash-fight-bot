# plugins/start.py
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
        [InlineKeyboardButton("🎵 Audio Controls", callback_data="menu_audio"),
         InlineKeyboardButton("🎛️ Audio Effects", callback_data="menu_fx")],
        [InlineKeyboardButton("📱 My Accounts", callback_data="menu_acc"),
         InlineKeyboardButton("📊 Utility & Status", callback_data="menu_util")],
        [InlineKeyboardButton("👤 Owner", url="https://t.me/"),
         InlineKeyboardButton("📖 Help Guide", callback_data="menu_help")]
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
        [InlineKeyboardButton("📱 Login via Phone (OTP)", callback_data="acc_login"), InlineKeyboardButton("🎙️ Set Recorder (String)", callback_data="acc_rec")],
        [InlineKeyboardButton("➕ Add Broadcaster", callback_data="acc_add"), InlineKeyboardButton("📋 View Saved Accounts", callback_data="acc_view")],
        [InlineKeyboardButton("🗑️ Delete Account", callback_data="acc_del"), InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_main")]
    ])

def utility_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏓 Ping Latency", callback_data="util_ping"), InlineKeyboardButton("📊 System Stats", callback_data="util_stats")],
        [InlineKeyboardButton("🔗 Active Forward List", callback_data="util_list"), InlineKeyboardButton("🆔 My ID & Info", callback_data="util_id")],
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_main")]
    ])

def owner_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Approve User", callback_data="own_approve"), InlineKeyboardButton("❌ Remove Access", callback_data="own_remove")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="own_ban"), InlineKeyboardButton("🟢 Unban User", callback_data="own_unban")],
        [InlineKeyboardButton("📋 View All DB Users", callback_data="own_users"), InlineKeyboardButton("🔄 Restart Bot", callback_data="own_restart")],
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_main")]
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

    is_owner = (user_id == Config.OWNER_ID)
    await message.reply_text(
        f"✨ <b>Welcome to Audio Forwarder</b> ✨\n\n"
        f"👋 Hello, {message.from_user.first_name}!\n"
        f"Use the buttons below to control your audio pipeline.",
        reply_markup=main_menu(is_owner)
    )

# ROUTER - Only matches menu_* and feature_* to avoid conflicting with owner.py
@Client.on_callback_query(filters.regex(r"^(menu_|audio_|fx_|acc_|util_|own_|noop)"))
async def menu_router(client, query: CallbackQuery):
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    user = await db.get_user(user_id)
    is_owner = (user_id == Config.OWNER_ID)

    try:
        if data == "menu_main":
            await query.message.edit_text(
                "✨ <b>Main Menu</b> ✨\n\nSelect a category below:",
                reply_markup=main_menu(is_owner)
            )
        elif data == "menu_audio":
            await query.message.edit_text("🎵 <b>Audio Controls</b>\nSelect an option:", reply_markup=audio_menu())
        elif data == "menu_fx":
            await query.message.edit_text("🎛️ <b>Audio Effects</b>\nSelect an effect to adjust:", reply_markup=effects_menu(user))
        elif data == "menu_acc":
            await query.message.edit_text("📱 <b>My Accounts</b>\nManage your userbots:", reply_markup=accounts_menu())
        elif data == "menu_util":
            await query.message.edit_text("📊 <b>Utility & Status</b>\nSelect an option:", reply_markup=utility_menu())
        elif data == "menu_owner" and is_owner:
            await query.message.edit_text("👑 <b>Owner Panel</b>\nAdmin controls:", reply_markup=owner_menu())
        elif data == "menu_help":
            await query.message.edit_text("📖 <b>Help Guide</b>\n\nUse the buttons to navigate.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Back to Main Menu", callback_data="menu_main")]]))
        elif data == "noop":
            await query.answer("Waiting for admin approval...", show_alert=True)
        else:
            # Sub-action placeholders (coming in next update)
            await query.answer("This feature is coming soon!", show_alert=True)
            
    except MessageNotModified:
        pass
    except Exception as e:
        print(f"Callback Error: {e}")
