# ─────────────────────────────────────────────
# REQUIRED — Bot must not start without these
# ─────────────────────────────────────────────
BOT_TOKEN = ""                                   # From @BotFather
API_ID = ""                                      # From my.telegram.org (integer)
API_HASH = ""                                    # From my.telegram.org
CHANNEL_ID = ""                                  # DB channel e.g. -1001234567890
OWNER = ""                                       # Your Telegram user ID (integer)
DB_URL = ""                                      # MongoDB connection string
DB_NAME = "yue"                                  # MongoDB database name

# ─────────────────────────────────────────────
# OPTIONAL — Admins (space-separated IDs)
# ─────────────────────────────────────────────
ADMINS = ""                                      # e.g. "111111 222222"

# ─────────────────────────────────────────────
# OTHER CONFIG
# ─────────────────────────────────────────────
AUTO_DELETE = ""                                 # Seconds before files are deleted (blank = off)
PROTECT = "False"                                # Prevent forwarding. True or False
CUSTOM_CAPTION = ""                              # Supports {filename}, {filesize}, {previouscaption}
CHANNEL_BUTTON = "True"                          # Show link button on DB channel posts

# ─────────────────────────────────────────────
# TOKEN / SHORTENER SYSTEM
# ─────────────────────────────────────────────
SHORTENER = "True"                               # True or False
SHORTENER_SITE = ""                              # e.g. publicearn.com  (no https://)
SHORTENER_API = ""                               # API key from shortener site
HOW_TO_DOWNLOAD = ""                             # Tutorial button URL e.g. https://t.me/yourchannel/5
SHORTENER_PREMIUM = "False"                      # True = premium users bypass shortener

# ─────────────────────────────────────────────
# DOMAIN (optional custom link domain)
# ─────────────────────────────────────────────
DOMAIN = ""

# ─────────────────────────────────────────────
# NORMAL FSUB
# ─────────────────────────────────────────────
FSUB = ""                                        # Space-separated channel IDs e.g. "-100111 -100222"
FSUB_LINKS = ""                                  # Respective invite links (same order as FSUB)
FSUB_TIMEOUT = "0"                               # Seconds before rotating FSUB links (0 = off)

# ─────────────────────────────────────────────
# FAKE BUTTONS
# ─────────────────────────────────────────────
FAKE = ""                                        # Comma-separated name=url pairs e.g. "Join=https://t.me/x,Rules=https://t.me/y"

# ─────────────────────────────────────────────
# REQUEST FSUB
# ─────────────────────────────────────────────
TOGGLE = "False"                                 # True or False to enable Request FSUB
REQUEST_FSUB = ""                                # Space-separated channel IDs
REQUEST_LINKS = ""                               # Respective invite links (same order)
SESSION = ""                                     # Pyrogram user session string (required for Request FSUB)

# ─────────────────────────────────────────────
# UPSTREAM REPO (auto-update on start)
# ─────────────────────────────────────────────
UPSTREAM_REPO = ""                               # Your GitHub repo URL with PAT e.g. https://ghp_xxx@github.com/user/repo
UPSTREAM_BRANCH = "main"

# ─────────────────────────────────────────────
# SERVER
# NOTE: Do NOT set PORT on Heroku — Heroku injects $PORT automatically.
# Only set PORT if self-hosting (Docker / VPS).
# ─────────────────────────────────────────────
# PORT = "8084"
