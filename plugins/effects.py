# plugins/effects.py
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.mongo import db
from config import Config

EFFECT_NAMES = {"level": "Level", "bass": "Bass", "treble": "Treble", "gain": "Gain", "overdrive": "Overdrive"}

@Client.on_message(filters.command("bass") & filters.private)
async def bass_cmd(client, message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user.get("is_approved") and user_id != Config.OWNER_ID:
        return await message.reply_text("⛔ Access restricted.")
    try:
        value = int(message.command[1])
        await db.update_effect(user_id, "bass", value)
        await message.reply_text(f"🎛️ Bass set to **{value}**")
    except (IndexError, ValueError):
        await message.reply_text("Usage: <code>/bass &lt;0-100&gt;</code>")

@Client.on_callback_query(filters.regex(r"^fx_"))
async def fx_callback(client, query: CallbackQuery):
    await query.answer()
    user_id = query.from_user.id
    action = query.data.split("_", 1)[1]

    if action == "reset":
        await db.reset_effects(user_id)
        return await query.message.edit_text("🔄 <b>All effects reset to default!</b>")

    if action == "show":
        user = await db.get_user(user_id)
        fx = user.get("effects", {})
        text = (
            "📋 <b>Active Effects</b>\n\n"
            f"🔊 Level: {fx.get('level', 100)}%\n"
            f"🎸 Bass: {fx.get('bass', 0)}%\n"
            f"🎻 Treble: {fx.get('treble', 0)}%\n"
            f"⚡ Gain: {fx.get('gain', 0)}%\n"
            f"🔥 Overdrive: {fx.get('overdrive', 0)}%\n"
            f"🗣️ Echo: {fx.get('echo', 'off')}"
        )
        return await query.message.edit_text(text)

    if action in EFFECT_NAMES:
        name = EFFECT_NAMES[action]
        try:
            # FIXED: use client.ask() — pyromod's primary, tested method
            response = await client.ask(
                query.message.chat.id,
                f"🎛️ <b>Send a number (0-100) for {name}:</b>\n\nType /cancel to abort.",
                timeout=60
            )
            if response.text.strip().lower() == "/cancel":
                return await response.reply_text("❌ Cancelled.")
            value = int(response.text.strip())
            if not 0 <= value <= 100:
                raise ValueError
            await db.update_effect(user_id, action, value)
            await response.reply_text(f"✅ <b>{name} set to {value}%!</b>")
        except (asyncio.TimeoutError, ValueError):
            await query.message.reply_text("❌ Invalid input or timeout.")
        return