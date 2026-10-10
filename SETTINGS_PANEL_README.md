# 🎛 Telegram Settings Panel — /us command

This patch replaces the static `.env`-based runtime configuration with a
**dynamic MongoDB-backed settings panel** accessible via `/us` in the bot's
private chat.

---

## 📁 New / Modified Files

| File | Role |
|------|------|
| `settings_db.py` | MongoDB read/write layer, type helpers, category metadata |
| `settings_ui.py` | Keyboard builders and message text generators |
| `plugins/user_settings.py` | `/us` command handler + all callback/conversation flows |
| `var.py` | **Modified** — secrets stay in `config.env`; runtime values now come from MongoDB |
| `bot.py` | **Modified** — reads live settings at startup instead of import-time constants |

---

## 🚀 How to Deploy

### 1. Drop the files in
Copy the three new files alongside your existing project:
```
settings_db.py
settings_ui.py
plugins/user_settings.py
```
Then replace `var.py` and `bot.py` with the updated versions.

### 2. Keep `config.env` for secrets only
The following stay in `config.env` and are **never** stored in MongoDB:
```
BOT_TOKEN, API_ID, API_HASH, OWNER, ADMINS, DB_URL, DB_NAME
UPSTREAM_REPO, UPSTREAM_BRANCH, DOMAIN
```

### 3. First-run migration
On first start, `var.py` automatically reads every runtime setting from
`config.env` and writes it into MongoDB. After that, `config.env` values
for runtime settings are ignored.

---

## 🎮 Using the Panel

Send `/us` in the bot's private DM (owner/admin only).

```
Main Panel
├── 📡 FSUB Settings      ← sub-panel with current values + edit/toggle buttons
├── 🔐 Request FSUB
├── 🗄 Database
├── ⚙️ Other Config
├── 🔑 Token System
├── 🎭 Fake Buttons
└── ❌ Close Panel
```

### Boolean settings
A single tap toggles ON/OFF instantly — no restart needed for the stored
value. The bot reads the DB value at each request.

### String / ID settings
Tap **✏️ Edit** → bot prompts for a new value → send it as a plain message.
The panel auto-refreshes after saving. Press **Cancel** to abort.

### Reset
Each sub-panel has a **🔄 Reset to Defaults** button that reverts all fields
in that category to their coded defaults after a confirmation step.

---

## ⚡ Hot-reload vs Restart

| Setting type | Takes effect |
|---|---|
| Boolean toggles (PROTECT, SHORTENER, …) | Immediately — read from DB per request |
| String/text values (CUSTOM_CAPTION, …)  | Immediately — read from DB per request |
| Structural changes (FSUB channels, CHANNEL_ID) | After bot restart — these are resolved at `bot.start()` |

---

## 🔒 Permissions

Only users whose Telegram ID is in `OWNER` or `ADMINS` (from `config.env`)
can open or interact with the settings panel. Everyone else gets a
`🚫 Access denied` alert.

---

## 📦 MongoDB Schema

Settings are stored in a single document in the `bot_settings` collection:
```json
{
  "_id": "settings",
  "FSUB": "-1002468017804 -1002204497798",
  "PROTECT": "False",
  "SHORTENER": "True",
  ...
}
```

All values are stored as strings for consistency and simplicity.
