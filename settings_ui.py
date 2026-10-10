from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from settings_db import CATEGORIES, FIELD_META, DEFAULTS, get_setting, as_bool


# ─── Helper: short display value ─────────────────────────────────────────────
def _display(key: str) -> str:
    val = get_setting(key)
    meta = FIELD_META.get(key, {})
    vtype = meta.get("type", "text")

    if not val or val == DEFAULTS.get(key, ""):
        marker = "✏️ (default)"
    elif vtype == "bool":
        marker = "✅ ON" if val.lower() == "true" else "❌ OFF"
    elif vtype == "secret":
        marker = f"🔒 {'*' * min(len(val), 8)}"
    elif len(val) > 30:
        marker = val[:27] + "…"
    else:
        marker = val
    return marker


# ─── Main panel ──────────────────────────────────────────────────────────────
def main_panel_text() -> str:
    lines = [
        "⚙️ **Bot Settings Panel**\n",
        "Choose a category to view or edit settings.",
        "Only owners and admins can make changes.\n",
    ]
    for ckey, cmeta in CATEGORIES.items():
        lines.append(f"{cmeta['label']}")
    return "\n".join(lines)


def main_panel_keyboard() -> InlineKeyboardMarkup:
    rows = []
    cat_items = list(CATEGORIES.items())
    # Two-column layout
    for i in range(0, len(cat_items), 2):
        row = []
        for ckey, cmeta in cat_items[i : i + 2]:
            row.append(InlineKeyboardButton(cmeta["label"], callback_data=f"us:cat:{ckey}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("❌ Close Panel", callback_data="us:close")])
    return InlineKeyboardMarkup(rows)


# ─── Category panel ───────────────────────────────────────────────────────────
def category_panel_text(ckey: str) -> str:
    cmeta = CATEGORIES[ckey]
    lines = [f"{cmeta['label']} — Settings\n"]
    for field in cmeta["fields"]:
        fmeta = FIELD_META[field]
        val = _display(field)
        lines.append(f"• **{fmeta['label']}**: `{val}`")
    return "\n".join(lines)


def category_panel_keyboard(ckey: str) -> InlineKeyboardMarkup:
    cmeta = CATEGORIES[ckey]
    rows = []
    for field in cmeta["fields"]:
        fmeta = FIELD_META.get(field, {})
        vtype = fmeta.get("type", "text")
        label = fmeta.get("label", field)

        if vtype == "bool":
            current = as_bool(field)
            btn_label = f"{'✅' if current else '❌'} {label}: {'ON' if current else 'OFF'}"
            rows.append([InlineKeyboardButton(btn_label, callback_data=f"us:toggle:{field}:{ckey}")])
        else:
            rows.append([InlineKeyboardButton(f"✏️ Edit {label}", callback_data=f"us:edit:{field}:{ckey}")])

    rows.append([
        InlineKeyboardButton("🔄 Reset to Defaults", callback_data=f"us:reset:{ckey}"),
        InlineKeyboardButton("◀️ Back", callback_data="us:main"),
    ])
    rows.append([InlineKeyboardButton("❌ Close Panel", callback_data="us:close")])
    return InlineKeyboardMarkup(rows)


# ─── Edit prompt ──────────────────────────────────────────────────────────────
def edit_prompt_text(field: str) -> str:
    fmeta = FIELD_META.get(field, {})
    current = get_setting(field)
    lines = [
        f"✏️ **Editing: {fmeta.get('label', field)}**\n",
        f"**Hint:** {fmeta.get('hint', 'Enter new value')}",
        f"**Current value:** `{current or '(empty)'}`\n",
        "Send the new value as a message, or press **Cancel** to go back.",
    ]
    return "\n".join(lines)


def edit_cancel_keyboard(field: str, ckey: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Cancel", callback_data=f"us:cat:{ckey}")
    ]])


# ─── Confirm reset ────────────────────────────────────────────────────────────
def reset_confirm_keyboard(ckey: str) -> InlineKeyboardMarkup:
    cmeta = CATEGORIES[ckey]
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Yes, reset", callback_data=f"us:resetconfirm:{ckey}"),
        InlineKeyboardButton("❌ No, go back", callback_data=f"us:cat:{ckey}"),
    ]])


def reset_confirm_text(ckey: str) -> str:
    cmeta = CATEGORIES[ckey]
    fields = cmeta["fields"]
    return (
        f"⚠️ **Reset {cmeta['label']}?**\n\n"
        f"This will reset **{len(fields)} setting(s)** to their default values.\n"
        "Are you sure?"
    )
