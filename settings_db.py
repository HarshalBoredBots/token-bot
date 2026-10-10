from pymongo import MongoClient
import logging
import os

logger = logging.getLogger(__name__)

# ─── Lazy MongoDB connection ──────────────────────────────────────────────────
_client = None
_db     = None
_scol   = None

def _get_col():
    global _client, _db, _scol
    if _scol is not None:
        return _scol
    from dotenv import load_dotenv
    load_dotenv("config.env", override=True)
    db_url  = os.environ.get("DB_URL", "")
    db_name = os.environ.get("DB_NAME", "filestore")
    if not db_url:
        raise RuntimeError("DB_URL is empty — check config.env")
    _client = MongoClient(db_url)
    _db     = _client[db_name]
    _scol   = _db["bot_settings"]
    return _scol

# ─── Default values ───────────────────────────────────────────────────────────
DEFAULTS = {
    "FSUB":              "",
    "FSUB_LINKS":        "",
    "FSUB_TIMEOUT":      "0",
    "TOGGLE":            "False",
    "REQUEST_FSUB":      "",
    "REQUEST_LINKS":     "",
    "SESSION":           "",
    "CHANNEL_ID":        "",
    "AUTO_DELETE":       "0",
    "PROTECT":           "False",
    "CUSTOM_CAPTION":    "",
    "CHANNEL_BUTTON":    "True",
    "SHORTENER":         "True",
    "SHORTENER_SITE":    "speedlinkurl.com",
    "SHORTENER_API":     "",
    "HOW_TO_DOWNLOAD":   "",
    "SHORTENER_PREMIUM": "True",
    "FAKE":              "",
}

# ─── Metadata ─────────────────────────────────────────────────────────────────
FIELD_META = {
    "FSUB":             {"label": "FSUB Channels",              "type": "ids",    "hint": "Space-separated channel IDs, e.g. -100123 -100456"},
    "FSUB_LINKS":       {"label": "FSUB Links",                 "type": "list",   "hint": "Space-separated invite links (same order as FSUB)"},
    "FSUB_TIMEOUT":     {"label": "FSUB Timeout (sec)",         "type": "int",    "hint": "Seconds before re-checking (0 = always check)"},
    "TOGGLE":           {"label": "Request FSUB Toggle",        "type": "bool",   "hint": "Enable/disable Request Force-Sub"},
    "REQUEST_FSUB":     {"label": "Request FSUB Channels",      "type": "ids",    "hint": "Space-separated channel IDs"},
    "REQUEST_LINKS":    {"label": "Request FSUB Links",         "type": "list",   "hint": "Invite links (same order as REQUEST_FSUB)"},
    "SESSION":          {"label": "User Session String",        "type": "secret", "hint": "Pyrogram session string for Request FSUB"},
    "CHANNEL_ID":       {"label": "DB Channel ID",              "type": "id",     "hint": "Single channel ID used as file store"},
    "AUTO_DELETE":      {"label": "Auto-Delete (sec)",          "type": "int",    "hint": "Delete files after N seconds (0 = off)"},
    "PROTECT":          {"label": "Protect from Forward",       "type": "bool",   "hint": "Prevent users from forwarding files"},
    "CUSTOM_CAPTION":   {"label": "Custom Caption",             "type": "text",   "hint": "Supports {filename}, {filesize}, {previouscaption}"},
    "CHANNEL_BUTTON":   {"label": "Channel Button",             "type": "bool",   "hint": "Show channel button under files"},
    "SHORTENER":        {"label": "Shortener Enabled",          "type": "bool",   "hint": "Wrap download links with shortener"},
    "SHORTENER_SITE":   {"label": "Shortener Site",             "type": "text",   "hint": "Domain, e.g. publicearn.com"},
    "SHORTENER_API":    {"label": "Shortener API Key",          "type": "secret", "hint": "API key from shortener site"},
    "HOW_TO_DOWNLOAD":  {"label": "How-To-Download URL",        "type": "url",    "hint": "Telegram post link for tutorial button"},
    "SHORTENER_PREMIUM":{"label": "Skip Shortener for Premium", "type": "bool",   "hint": "Premium users bypass shortener"},
    "FAKE":             {"label": "Fake Buttons",               "type": "csv",    "hint": "Comma-separated name=url pairs"},
}

CATEGORIES = {
    "fsub":     {"label": "📡 FSUB Settings",   "fields": ["FSUB", "FSUB_LINKS", "FSUB_TIMEOUT"]},
    "reqfsub":  {"label": "🔐 Request FSUB",    "fields": ["TOGGLE", "REQUEST_FSUB", "REQUEST_LINKS", "SESSION"]},
    "database": {"label": "🗄 Database",         "fields": ["CHANNEL_ID"]},
    "other":    {"label": "⚙️ Other Config",     "fields": ["AUTO_DELETE", "PROTECT", "CUSTOM_CAPTION", "CHANNEL_BUTTON"]},
    "token":    {"label": "🔑 Token System",     "fields": ["SHORTENER", "SHORTENER_SITE", "SHORTENER_API", "HOW_TO_DOWNLOAD", "SHORTENER_PREMIUM"]},
    "fake":     {"label": "🎭 Fake Buttons",     "fields": ["FAKE"]},
}

# ─── In-memory cache ──────────────────────────────────────────────────────────
_cache: dict = {}

def _load_from_db() -> dict:
    col = _get_col()
    doc = col.find_one({"_id": "settings"})
    if not doc:
        doc = {"_id": "settings", **DEFAULTS}
        col.insert_one(doc)
    return doc

def _ensure_loaded():
    global _cache
    if not _cache:
        _cache = _load_from_db()

def get_setting(key: str) -> str:
    _ensure_loaded()
    return str(_cache.get(key, DEFAULTS.get(key, "")))

def set_setting(key: str, value: str) -> bool:
    global _cache
    _ensure_loaded()
    try:
        _get_col().update_one({"_id": "settings"}, {"$set": {key: value}}, upsert=True)
        _cache[key] = value
        logger.info(f"[SETTINGS] Updated {key} = {value!r}")
        return True
    except Exception as e:
        logger.error(f"[SETTINGS] Failed to update {key}: {e}")
        return False

def reset_category(category_key: str) -> bool:
    fields = CATEGORIES[category_key]["fields"]
    updates = {f: DEFAULTS.get(f, "") for f in fields}
    try:
        _get_col().update_one({"_id": "settings"}, {"$set": updates}, upsert=True)
        _cache.update(updates)
        return True
    except Exception as e:
        logger.error(f"[SETTINGS] Failed to reset {category_key}: {e}")
        return False

def get_all_settings() -> dict:
    _ensure_loaded()
    return dict(_cache)

def invalidate_cache():
    global _cache
    _cache = {}

# ─── Typed accessors ─────────────────────────────────────────────────────────
def as_bool(key: str) -> bool:
    return get_setting(key).strip().lower() == "true"

def as_int(key: str) -> int:
    try:
        return int(get_setting(key) or 0)
    except ValueError:
        return 0

def as_id_list(key: str) -> list:
    raw = get_setting(key).strip()
    if not raw:
        return []
    try:
        return [int(x) for x in raw.split()]
    except ValueError:
        return []

def as_str_list(key: str) -> list:
    raw = get_setting(key).strip()
    return [x for x in raw.split() if x]

def as_csv_list(key: str) -> list:
    raw = get_setting(key).strip()
    return [i.strip() for i in raw.split(",") if i.strip()]
