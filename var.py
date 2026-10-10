from dotenv import load_dotenv
import os
import logging
from logging.handlers import RotatingFileHandler
import pytz

load_dotenv("config.env", override=True)

# ── Secrets (stay in config.env) ──────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID    = os.environ.get("API_ID", "")
API_HASH  = os.environ.get("API_HASH", "")
OWNER     = [int(x) for x in os.environ.get("OWNER", "").split()]
ADMINS    = [int(x) for x in os.environ.get("ADMINS", "").split()]
DB_URL    = os.environ.get("DB_URL", "")
DB_NAME   = os.environ.get("DB_NAME", "filestore")

DOMAIN         = os.environ.get("DOMAIN", "")
PORT           = os.environ.get("PORT", "8084")
CURRENT_REPO   = os.environ.get("UPSTREAM_REPO", "")
CURRENT_BRANCH = os.environ.get("UPSTREAM_BRANCH", "")

if DOMAIN:
    DOMAIN = DOMAIN if DOMAIN.endswith("/") else DOMAIN + "/"

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=50_000_000, backupCount=10),
        logging.StreamHandler(),
    ],
)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

TIME_ZONE = pytz.timezone("Asia/Kolkata")

# ── Runtime settings from MongoDB ─────────────────────────────────────────────
from settings_db import (
    get_setting, as_bool, as_int, as_id_list, as_str_list, as_csv_list,
)

def _channel_id():
    raw = get_setting("CHANNEL_ID").strip()
    if raw:
        try:
            return int(raw)
        except (ValueError, TypeError):
            pass
    try:
        return int(os.environ.get("CHANNEL_ID", "0"))
    except ValueError:
        return 0

_DYNAMIC = {
    "FSUB":              lambda: as_id_list("FSUB"),
    "FSUB_LINKS":        lambda: as_str_list("FSUB_LINKS"),
    "FSUB_TIMEOUT":      lambda: as_int("FSUB_TIMEOUT"),
    "TOGGLE":            lambda: as_bool("TOGGLE"),
    "REQUEST_FSUB":      lambda: as_id_list("REQUEST_FSUB"),
    "REQUEST_LINKS":     lambda: as_str_list("REQUEST_LINKS"),
    "SESSION":           lambda: get_setting("SESSION"),
    "CHANNEL_ID":        _channel_id,
    "AUTO_DELETE":       lambda: as_int("AUTO_DELETE"),
    "PROTECT":           lambda: as_bool("PROTECT"),
    "CUSTOM_CAPTION":    lambda: get_setting("CUSTOM_CAPTION"),
    "CHANNEL_BUTTON":    lambda: as_bool("CHANNEL_BUTTON"),
    "SHORTENER":         lambda: as_bool("SHORTENER"),
    "SHORTENER_SITE":    lambda: get_setting("SHORTENER_SITE"),
    "SHORTENER_API":     lambda: get_setting("SHORTENER_API"),
    "HOW_TO_DOWNLOAD":   lambda: get_setting("HOW_TO_DOWNLOAD"),
    "SHORTENER_PREMIUM": lambda: as_bool("SHORTENER_PREMIUM"),
    "FAKE":              lambda: as_csv_list("FAKE"),
}

# ── One-time migration: seed config.env → MongoDB if DB has no data ───────────
def _seed_from_env():
    from settings_db import _get_col, DEFAULTS, invalidate_cache
    col = _get_col()
    doc = col.find_one({"_id": "settings"})
    if doc and any(doc.get(k, "") not in ("", None) for k in DEFAULTS):
        return  # Already has data
    env_map = {
        "FSUB":              os.environ.get("FSUB", ""),
        "FSUB_LINKS":        os.environ.get("FSUB_LINKS", ""),
        "FSUB_TIMEOUT":      os.environ.get("FSUB_TIMEOUT", "0"),
        "TOGGLE":            os.environ.get("TOGGLE", "False"),
        "REQUEST_FSUB":      os.environ.get("REQUEST_FSUB", ""),
        "REQUEST_LINKS":     os.environ.get("REQUEST_LINKS", ""),
        "SESSION":           os.environ.get("SESSION", ""),
        "CHANNEL_ID":        os.environ.get("CHANNEL_ID", ""),
        "AUTO_DELETE":       os.environ.get("AUTO_DELETE", "0"),
        "PROTECT":           os.environ.get("PROTECT", "False"),
        "CUSTOM_CAPTION":    os.environ.get("CUSTOM_CAPTION", ""),
        "CHANNEL_BUTTON":    os.environ.get("CHANNEL_BUTTON", "True"),
        "SHORTENER":         os.environ.get("SHORTENER", "True"),
        "SHORTENER_SITE":    os.environ.get("SHORTENER_SITE", ""),
        "SHORTENER_API":     os.environ.get("SHORTENER_API", ""),
        "HOW_TO_DOWNLOAD":   os.environ.get("HOW_TO_DOWNLOAD", ""),
        "SHORTENER_PREMIUM": os.environ.get("SHORTENER_PREMIUM", "True"),
        "FAKE":              os.environ.get("FAKE", ""),
    }
    updates = {k: v for k, v in env_map.items() if v}
    if updates:
        col.update_one({"_id": "settings"}, {"$set": updates}, upsert=True)
        invalidate_cache()
        logging.getLogger(__name__).info(
            f"[var] Seeded {len(updates)} settings from config.env into MongoDB."
        )

_seed_from_env()

# ── Module __getattr__: `from var import FSUB` resolves live from DB ──────────
import sys as _sys

class _DynamicModule(_sys.modules[__name__].__class__):
    def __getattr__(self, name):
        if name in _DYNAMIC:
            return _DYNAMIC[name]()
        raise AttributeError(f"module 'var' has no attribute {name!r}")

_sys.modules[__name__].__class__ = _DynamicModule

# Make `from var import *` include all dynamic names
__all__ = [
    # Secrets
    "BOT_TOKEN", "API_ID", "API_HASH", "OWNER", "ADMINS",
    "DB_URL", "DB_NAME", "DOMAIN", "PORT", "CURRENT_REPO", "CURRENT_BRANCH",
    "LOGGER", "TIME_ZONE",
    # Dynamic (resolved via __getattr__ at access time)
    "FSUB", "FSUB_LINKS", "FSUB_TIMEOUT",
    "TOGGLE", "REQUEST_FSUB", "REQUEST_LINKS", "SESSION",
    "CHANNEL_ID", "AUTO_DELETE", "PROTECT", "CUSTOM_CAPTION", "CHANNEL_BUTTON",
    "SHORTENER", "SHORTENER_SITE", "SHORTENER_API", "HOW_TO_DOWNLOAD", "SHORTENER_PREMIUM",
    "FAKE",
    # Helpers
    "_DYNAMIC",
]
