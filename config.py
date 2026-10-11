import os

# REQUIRED
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = "20140875"
API_HASH = "a06fa97d5a853ec2da79015b11335a17"
CHANNEL_ID = "-1003968507170"                                  # Database Channels
OWNER = "1828405916"                                           # Bot Owners Who Can Broadcast , Seperate By Space
ADMINS = "7719103435 8674351020 1828405916 7025079982 5004882077 7820346667 7821627725"  # Bot Admins Who Can Generate Links , Seperate By Space
DB_URL = os.environ.get("DB_URL", "")                         # MongoDB Url
DB_NAME = os.environ.get("DB_NAME", "yue")

# OTHER CONFIG
AUTO_DELETE = ""
PROTECT = "False"                                # Protect From Forwarding , Default False
CUSTOM_CAPTION = ""                              # Supports {filename} , {previouscaption} , {filesize}
CHANNEL_BUTTON = "True"

# TOKEN SYSTEM
SHORTENER = "True"                               # True or False To Enable Shortener
SHORTENER_SITE = "http://iskerts.com/"           # Shortener Site Like publicearn.com
SHORTENER_API = "3710cb9dac5166b3a348d825c00f40bf28d0ac7e"   # Shortener API
HOW_TO_DOWNLOAD = "https://t.me/Gooner_Ocean/9"
SHORTENER_PREMIUM = "False"                      # True/False For Adding Premium Users

# DOMAIN
DOMAIN = ""

#NORMAL FSUB
FSUB = ""
FSUB_LINKS = ""
FSUB_TIMEOUT = "0"

# FAKE Buttons
FAKE = ""

#REQUEST_FSUB
TOGGLE = ""                                      # Set True or False To Enable or Disable Request Fsub
REQUEST_FSUB = ""                                # ID of Channels For Request Fsub , Seperated By Spaces
REQUEST_LINKS = ""                               # Respective Links Of Request Fsub In Same Order
SESSION = ""                                     # Session (Optional If Not Using Request FSUB)

# Master Repo Details
UPSTREAM_REPO = "https://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@github.com/kakashimeow/ocehen1new"
UPSTREAM_BRANCH = "main"
PORT = "8084"

# ─────────────────────────────────────────────
# Startup validation
# ─────────────────────────────────────────────

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN env var is not set. Add it in the Heroku dashboard.")

if not DB_URL:
    raise ValueError("DB_URL env var is not set. Add it in the Heroku dashboard.")
