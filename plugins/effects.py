# plugins/effects.py
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.mongo import db
from config import Config
from core.audio_dsp import AudioDSP # We will use this to reload FFmpeg

@Client.on_message(filters.command("bass") & filters.private)
async def bass_cmd(client, message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user.get("is_approved") and user_id != Config.OWNER_ID:
        return await message.reply_text("⛔ Access restricted.")
    try:
        value = int(message.command[1])
        await db.update_effect(user_id, "bass", value)
        await message.reply_text(f"🎛️ Bass set to **{value}**\nReloading audio stream...")
        # In a real implementation, you would call AudioDSP(user_id).reload_filters(user)
    except:
        await message.reply_text("Usage: `/bass <0-100>`")

# Callback for the Effects Menu buttons
@Client.on_callback_query(filters.regex(r"^fx_"))
async def fx_callback(client, query: CallbackQuery):
    await query.answer()
    user_id = query.from_user.id
    user = await db.get_user(user_id)
    action = query.data.split("_")[1]

    if action == "reset":
        await db.reset_effects(user_id)
        user = await db.get_user(user_id) # Refresh data
        await query.message.edit_text("🔄 **All effects reset to default!**")
        # Reload AudioDSP here
        return

    if action == "show":
        fx = user.get("effects", {})
        text = (
            "📋 **Active Effects**\n\n"
            f"🔊 Level: {fx.get('level')}%\n"
            f"🎸 Bass: {fx.get('bass')}%\n"
            f"🎻 Treble: {fx.get('treble')}%\n"
            f"⚡ Gain: {fx.get('gain')}%\n"
            f"🔥 Overdrive: {fx.get('overdrive')}%\n"
            f"🗣️ Echo: {fx.get('echo')}"
        )
        return await query.message.edit_text(text)

    # For prompts like Level, Bass, Treble, etc.
    prompt_text = f"🎛️ **Enter a value (0-100) for {action.capitalize()}:**\n\n*(Send as a reply to this message)*"
    
    # Use pyromod to ask for input
    try:
        answer = await client.ask(query.message.chat.id, prompt_text, timeout=60)
        value = int(answer.text)
        if not 0 <= value <= 100:
            raise ValueError
        await db.update_effect(user_id, action, value)
        await answer.reply_text(f"✅ {action.capitalize()} set to **{value}%**!")
        # Reload AudioDSP here
    except (ValueError, TimeoutError):
        await query.message.reply_text("❌ Invalid input or timeout. Please try again from the menu.")