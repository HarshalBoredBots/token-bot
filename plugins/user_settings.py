import asyncio
import logging
from datetime import datetime

from pyrogram import Client, filters, enums
from pyrogram.types import Message, CallbackQuery

from var import OWNER, ADMINS
from helper import replyMessage
from settings_db import (
    CATEGORIES, FIELD_META, DEFAULTS,
    get_setting, set_setting, reset_category, as_bool,
)
from settings_ui import (
    main_panel_text, main_panel_keyboard,
    category_panel_text, category_panel_keyboard,
    edit_prompt_text, edit_cancel_keyboard,
    reset_confirm_text, reset_confirm_keyboard,
)

logger = logging.getLogger(__name__)

def _is_owner_or_admin(user_id: int) -> bool:
    import var as _var
    return user_id in _var.OWNER or user_id in _var.ADMINS


_awaiting: dict[int, dict] = {}


@Client.on_message(filters.private & filters.command("us"))
async def cmd_user_settings(app: Client, message: Message):
    if not _is_owner_or_admin(message.from_user.id):
        return await message.reply("🚫 You don't have permission to access this panel.")
    sent = await message.reply(
        main_panel_text(),
        reply_markup=main_panel_keyboard(),
        parse_mode=enums.ParseMode.MARKDOWN,
        quote=True,
    )
    _awaiting.pop(message.from_user.id, None)


@Client.on_callback_query(filters.regex(r"^us:"))
async def handle_us_callback(app: Client, query: CallbackQuery):
    user_id = query.from_user.id

    if not _is_owner_or_admin(user_id):
        return await query.answer("🚫 Access denied.", show_alert=True)

    data = query.data
    parts = data.split(":")

    if parts[1] == "close":
        _awaiting.pop(user_id, None)
        await query.message.delete()
        return

    if parts[1] == "main":
        _awaiting.pop(user_id, None)
        await _safe_edit(query, main_panel_text(), main_panel_keyboard())
        return

    if parts[1] == "cat":
        ckey = parts[2]
        _awaiting.pop(user_id, None)
        await _safe_edit(query, category_panel_text(ckey), category_panel_keyboard(ckey))
        return

    if parts[1] == "toggle":
        field, ckey = parts[2], parts[3]
        current = as_bool(field)
        new_val = "False" if current else "True"
        ok = set_setting(field, new_val)
        if ok:
            await query.answer(f"{'✅ Enabled' if new_val == 'True' else '❌ Disabled'} {FIELD_META[field]['label']}")
            _log_change(user_id, field, new_val)
        else:
            await query.answer("⚠️ Failed to save setting.", show_alert=True)
        await _safe_edit(query, category_panel_text(ckey), category_panel_keyboard(ckey))
        return

    if parts[1] == "edit":
        field, ckey = parts[2], parts[3]
        _awaiting[user_id] = {
            "field": field,
            "ckey": ckey,
            "panel_msg_id": query.message.id,
            "chat_id": query.message.chat.id,
        }
        await _safe_edit(query, edit_prompt_text(field), edit_cancel_keyboard(field, ckey))
        return

    if parts[1] == "reset":
        ckey = parts[2]
        await _safe_edit(query, reset_confirm_text(ckey), reset_confirm_keyboard(ckey))
        return

    if parts[1] == "resetconfirm":
        ckey = parts[2]
        ok = reset_category(ckey)
        if ok:
            await query.answer(f"🔄 Reset {CATEGORIES[ckey]['label']} to defaults.")
            logger.info(f"[SETTINGS] User {user_id} reset category '{ckey}'")
        else:
            await query.answer("⚠️ Reset failed.", show_alert=True)
        await _safe_edit(query, category_panel_text(ckey), category_panel_keyboard(ckey))
        return

    await query.answer("Unknown action.", show_alert=True)


@Client.on_message(filters.private & ~filters.command([
    "start", "us", "help", "stats", "users", "log",
    "ban", "unban", "banlist", "broadcast", "change",
    "addpremium", "removepremium", "listpremium", "batch", "done", "batchx",
]), group=2)
async def handle_settings_input(app: Client, message: Message):
    user_id = message.from_user.id
    state = _awaiting.get(user_id)
    if not state:
        message.continue_propagation()
        return

    field = state["field"]
    ckey = state["ckey"]
    panel_msg_id = state["panel_msg_id"]
    chat_id = state["chat_id"]
    raw_input = message.text.strip() if message.text else ""

    error = _validate(field, raw_input)
    if error:
        err_msg = await message.reply(f"⚠️ {error}\n\nTry again or press **Cancel**.", parse_mode=enums.ParseMode.MARKDOWN)
        asyncio.get_event_loop().create_task(_auto_delete(err_msg, 8))
        return

    ok = set_setting(field, raw_input)
    await message.delete()
    _awaiting.pop(user_id, None)

    if ok:
        _log_change(user_id, field, raw_input)
        try:
            await app.edit_message_text(
                chat_id=chat_id,
                message_id=panel_msg_id,
                text=category_panel_text(ckey),
                reply_markup=category_panel_keyboard(ckey),
                parse_mode=enums.ParseMode.MARKDOWN,
            )
        except Exception as e:
            logger.warning(f"[SETTINGS] Could not edit panel after save: {e}")
    else:
        err_msg = await app.send_message(chat_id, "⚠️ Failed to save setting to database.")
        asyncio.get_event_loop().create_task(_auto_delete(err_msg, 5))


def _validate(field: str, value: str) -> str | None:
    meta = FIELD_META.get(field, {})
    vtype = meta.get("type", "text")

    if not value and field not in ("CUSTOM_CAPTION", "FAKE", "SESSION", "FSUB_LINKS", "REQUEST_LINKS"):
        return None

    if vtype == "bool":
        if value.lower() not in ("true", "false"):
            return "Please send `True` or `False`."

    elif vtype in ("id", "ids"):
        for part in value.split():
            try:
                int(part)
            except ValueError:
                return f"`{part}` is not a valid integer ID."

    elif vtype == "int":
        try:
            int(value)
        except ValueError:
            return "Please send a whole number (e.g. `0`, `300`)."

    elif vtype == "url":
        if value and not (value.startswith("http://") or value.startswith("https://")):
            return "Please send a valid URL starting with `http://` or `https://`."

    return None


async def _safe_edit(query: CallbackQuery, text: str, markup):
    try:
        await query.edit_message_text(text, reply_markup=markup, parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        logger.warning(f"[SETTINGS] edit_message_text failed: {e}")
    await query.answer()


async def _auto_delete(msg, delay: int):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


def _log_change(user_id: int, field: str, value: str):
    label = FIELD_META.get(field, {}).get("label", field)
    vtype = FIELD_META.get(field, {}).get("type", "text")
    display = ("*" * 8) if vtype == "secret" else value
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[SETTINGS CHANGE] [{ts}] user={user_id} field={field!r} ({label}) → {display!r}")