# Bug Fix Changelog

## Critical

| # | File | Fix |
|---|------|-----|
| 1 | `bot.py` | Renamed instance to `app` to avoid the class/instance name collision. `main.py` now imports `app`. |
| 2 | `main.py` | Removed `Bot.loop.run_forever()` which made `idle()` unreachable dead code. |
| 3 | `plugins/start.py` | Added `await` to `asyncio.gather()` inside `clean_messages` — without it messages were never deleted. |
| 4 | `helper.py` | Fixed `copyMessage` retry call: `protect` and `reply_markup` were shifted into the wrong slots (`caption` and `protect`). |
| 5 | `helper.py` | Rewrote XOR cipher to operate on raw bytes + base64 instead of `chr()`/`ord()` — the old approach produced non-ASCII codepoints that crashed `encode()`. |

## High

| # | File | Fix |
|---|------|-----|
| 6 | `plugins/start.py` | Added module-level `_broadcasting` flag to prevent concurrent `/broadcast` runs from racing over `users_list`. |
| 7 | `plugins/start.py` | BAN check now enforced at the top of `/start` — banned users were previously able to use the bot freely. |
| 8 | `helper.py` | FAKE button loop now validates each entry has an `=` separator before unpacking — malformed entries raised `ValueError`. |
| 9 | `db.py` | User list is now loaded lazily on first access (`_ensure_users_loaded`) instead of blocking with a synchronous MongoDB query at import time. Added `get_users_snapshot()` helper for safe iteration. |
| 10 | `update.py` | `environ.get("UPSTREAM_REPO")` now defaults to `""` — the original `len(None)` raised `TypeError` when the variable was missing. |
| 11 | `plugins/premium.py` | Expiry validation now happens **before** `calc_end()` is called, not after. |

## Medium / Minor

| # | File | Fix |
|---|------|-----|
| 12 | `plugins/start.py` | Broadcast now iterates `get_users_snapshot()` (a copy) — `del_user()` mutating the live list during iteration silently skipped users. |
| 13 | `plugins/start.py` | Banned users are filtered out of the broadcast recipient list. |
| 14 | `plugins/start.py` | FloodWait retry inside broadcast loop is now wrapped in its own `try/except` — an error on retry previously aborted the entire loop. |
| 15 | `plugins/start.py` | Added `await asyncio.sleep(0.05)` between broadcast sends (~20 msg/s) to reduce Telegram FloodWait accumulation. |
| 16 | `plugins/start.py` | Status message update interval changed from every 5 to every 20 users to reduce `editMessage` FloodWait on large lists. |
| 17 | `plugins/start.py` | Broadcast loop wrapped in `try/finally` so the status message is always deleted and final stats always sent even if an exception occurs. |
| 18 | `plugins/start.py` | `CUSTOM_CAPTION.format()` is now only called for `msg.document` or `msg.video` — prevents `AttributeError` on other media types and `None` substitution. |
| 19 | `plugins/start.py` | Bare `except:` replaced with `except Exception as e:` with logging throughout. |
| 20 | `plugins/start.py` | Hardcoded `https://t.me/Gooners_Ocean/…` channel URLs replaced with the configurable `HOW_TO_DOWNLOAD` setting. |
| 21 | `plugins/change.py` | `re.search()` result is now guarded — a missing `ghp_` PAT in the URL previously raised `AttributeError: 'NoneType'.group(0)`. |
| 22 | `plugins/fsub_timeout.py` | Switched to `app` instance; added per-channel `try/except` in `perform()` so one bad channel doesn't abort the whole rotation. |
| 23 | `plugins/premium.py` | Switched `Bot` reference to `app` instance; simplified `calc_end` with a dict dispatch. |
