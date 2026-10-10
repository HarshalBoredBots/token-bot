from var import *
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, ChannelInvalid, MessageIdInvalid
from pyrogram.errors import FloodWait
import base64
import asyncio
from db import *
import re
import aiohttp
from urllib.parse import quote


async def is_auth(_, client, update):
    import var as _var
    if update.from_user.id in _var.OWNER + _var.ADMINS:
        return True
    return False


async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string


async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    string = string_bytes.decode("ascii")
    return string


# FIX 5: XOR cipher now operates on raw bytes instead of characters.
# The original chr(ord(c) ^ ord(key[...])) approach produced codepoints > 127
# which then crashed ascii encode(). Byte-level XOR + base64 is safe.
async def xor_encrypt(data: str, key: str) -> bytes:
    data_bytes = data.encode("utf-8")
    key_bytes  = key.encode("utf-8")
    return bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data_bytes))


async def encoder(string: str, key: str) -> str:
    encrypted = await xor_encrypt(string, key)
    b64 = base64.urlsafe_b64encode(encrypted).decode("ascii").strip("=")
    return b64


async def decoder(string: str, key: str) -> str:
    string = string.strip("=")
    padded = string + "=" * (-len(string) % 4)
    encrypted = base64.urlsafe_b64decode(padded)
    key_bytes  = key.encode("utf-8")
    decrypted  = bytes(b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(encrypted))
    return decrypted.decode("utf-8")


async def readable_datetime(obj, only=False):
    if only:
        return obj.strftime("%d-%b")
    return obj.strftime("%d %b %Y, %I:%M %p")


async def gen_link(username, start, end=False):
    if end:
        to_encode = f"{start}-{end}"
    else:
        to_encode = f"{start}"
    encoded = await encode(to_encode)
    if DOMAIN:
        return f"{DOMAIN}{encoded}"
    return f"https://telegram.me/{username}?start={encoded}"


async def check_fsubs(app, ids):
    from var import _DYNAMIC
    FSUB = _DYNAMIC["FSUB"]()
    TOGGLE = _DYNAMIC["TOGGLE"]()
    REQUEST_FSUB = _DYNAMIC["REQUEST_FSUB"]()
    REQUEST_LINKS = _DYNAMIC["REQUEST_LINKS"]()

    async def is_subscribed(client, update, FORCE_SUB_CHANNEL):
        user_id = update
        try:
            member = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        except UserNotParticipant:
            return FORCE_SUB_CHANNEL, False
        except ChannelInvalid:
            return FORCE_SUB_CHANNEL, True
        if not member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]:
            return FORCE_SUB_CHANNEL, False
        else:
            return FORCE_SUB_CHANNEL, True

    reply_markup = []
    tasks = [is_subscribed(app, ids, f_id) for f_id in FSUB]
    status = await asyncio.gather(*tasks)
    for i in status:
        if not i[1]:
            reply_markup.append([InlineKeyboardButton('Join Channel', url=app.FSUB[i[0]])])

    if TOGGLE:
        async def is_subscribed_request(client, update, FORCE_SUB_CHANNEL):
            user_id = update
            for lst in app.PENDING[FORCE_SUB_CHANNEL]:
                if user_id == lst:
                    return FORCE_SUB_CHANNEL, True
            return await is_subscribed(client, update, FORCE_SUB_CHANNEL)

        tasks = [is_subscribed_request(app, ids, f_id) for f_id in REQUEST_FSUB]
        status = await asyncio.gather(*tasks)
        for index, i in enumerate(status):
            if not i[1]:
                reply_markup.append([InlineKeyboardButton('Join Channel', url=REQUEST_LINKS[index])])

    new_markup = [[]]
    for i in reply_markup:
        if len(new_markup[-1]) > 1:
            new_markup.append([i[0]])
        else:
            new_markup[-1].append(i[0])
    real_markup = [i for i in new_markup if i]
    stat = len(real_markup) != 0

    # FIX 13: Guard against malformed FAKE entries missing the '=' separator.
    # Previously a bare split('=') on a bad entry raised ValueError.
    if FAKE:
        for x in FAKE:
            parts = x.split('=', maxsplit=1)
            if len(parts) != 2:
                LOGGER(__name__).warning(f"[FAKE] Skipping malformed entry (no '='): {x!r}")
                continue
            name, link = parts[0].strip(), parts[1].strip()
            real_markup.append([InlineKeyboardButton(name, url=link)])

    return stat, real_markup


async def replyMessage(message, text, reply_markup=None):
    try:
        msg = await message.reply_text(text, reply_markup=reply_markup, quote=True)
        return msg
    except FloodWait as e:
        LOGGER(__name__).info(f"Sleeping for {e.value} Seconds")
        await asyncio.sleep(e.value * 1.5)
        return await replyMessage(message, text, reply_markup)


# FIX 4: copyMessage retry now passes all arguments in the correct order.
# Original retry call was: copyMessage(message, chat_id, protect, reply_markup)
# which put `protect` into the `caption` slot and `reply_markup` into `protect`.
async def copyMessage(message, chat_id, caption=None, protect=False, reply_markup=None):
    try:
        if not caption:
            if message.document or message.video:
                caption = message.caption
            else:
                caption = None
        msg = await message.copy(chat_id, caption=caption, reply_markup=reply_markup, protect_content=protect)
        return msg
    except FloodWait as e:
        LOGGER(__name__).info(f"Sleeping for {e.value} Seconds")
        await asyncio.sleep(e.value * 1.5)
        return await copyMessage(message, chat_id, caption, protect, reply_markup)


async def deleteMessage(message):
    try:
        await message.delete()
    except FloodWait as e:
        LOGGER(__name__).info(f"Sleeping for {e.value} Seconds")
        await asyncio.sleep(e.value * 1.5)
        return await deleteMessage(message)


async def editMessage(message, text, reply_markup=None):
    try:
        await message.edit_text(text, reply_markup)
    except FloodWait as e:
        LOGGER(__name__).info(f"Sleeping for {e.value} Seconds")
        await asyncio.sleep(e.value * 1.5)
        return await editMessage(message, text, reply_markup)


async def editReplyMarkup(message, reply_markup=None):
    try:
        await message.edit_reply_markup(reply_markup)
    except FloodWait as e:
        LOGGER(__name__).info(f"Sleeping for {e.value} Seconds")
        await asyncio.sleep(e.value * 1.5)
        return await editReplyMarkup(message, reply_markup)
    except MessageIdInvalid:
        LOGGER(__name__).warning(f"editReplyMarkup: message {message.id} not editable, skipping.")


async def get_readable_time(seconds: int) -> str:
    time_units = [
        ("year",  60 * 60 * 24 * 365),
        ("month", 60 * 60 * 24 * 30),
        ("day",   60 * 60 * 24),
        ("hour",  60 * 60),
        ("min",   60),
        ("sec",   1),
    ]
    time_list = []
    for unit, unit_seconds in time_units:
        if seconds >= unit_seconds:
            value, seconds = divmod(seconds, unit_seconds)
            time_list.append(f"{value}{unit}")
    return " : ".join(time_list)


async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == CHANNEL_ID:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = "https://t.me/(?:c/)?(.*)/(\\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(CHANNEL_ID):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0


async def get_old_format(argument):
    import var as _var
    OWNER = _var.OWNER
    CHANNEL_ID = _var.CHANNEL_ID
    if len(argument) == 3 and int(argument[1]) in OWNER:
        try:
            ids = [int(int(argument[2]) / abs(CHANNEL_ID))]
        except Exception:
            return
    elif len(argument) == 3 or len(argument) == 4:
        try:
            if int(argument[1]) in OWNER:
                start = int(int(argument[2]) / abs(CHANNEL_ID))
                end   = int(int(argument[3]) / abs(CHANNEL_ID))
            else:
                start = int(int(argument[1]) / abs(CHANNEL_ID))
                end   = int(int(argument[2]) / abs(CHANNEL_ID))
        except Exception:
            return
        if start <= end:
            ids = range(start, end + 1)
        else:
            ids = []
            i = start
            while True:
                ids.append(i)
                i -= 1
                if i < end:
                    break
    elif len(argument) == 2:
        try:
            ids = [int(int(argument[1]) / abs(CHANNEL_ID))]
        except Exception:
            return
    return ids


async def short_url(longurl):
    from var import _DYNAMIC
    site    = _DYNAMIC["SHORTENER_SITE"]().strip().rstrip("/")
    api_key = _DYNAMIC["SHORTENER_API"]()
    if not site or not api_key:
        LOGGER(__name__).warning("[SHORT_URL] SHORTENER_SITE or SHORTENER_API is empty, skipping.")
        return None
    if site.startswith("http://") or site.startswith("https://"):
        full_url = f"{site}/api?api={api_key}&url={quote(longurl)}"
    else:
        full_url = f"https://{site}/api?api={api_key}&url={quote(longurl)}"
    LOGGER(__name__).info(f"[SHORT_URL] Requesting: {full_url}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(full_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                raw = await response.text()
                LOGGER(__name__).info(f"[SHORT_URL] Status: {response.status} | Response: {raw[:300]}")
                try:
                    res = await response.json(content_type=None)
                except Exception as e:
                    LOGGER(__name__).error(f"[SHORT_URL] JSON parse failed: {e} | Raw: {raw[:200]}")
                    return None
                shorted = (
                    res.get("shortenedUrl")
                    or res.get("short_url")
                    or res.get("shortLink")
                    or res.get("shortened_url")
                    or ""
                )
                if not shorted:
                    LOGGER(__name__).warning(f"[SHORT_URL] No URL in response. Full response: {res}")
                    return None
                return shorted
    except aiohttp.ClientConnectorError as e:
        LOGGER(__name__).error(f"[SHORT_URL] Connection error: {e}")
        return None
    except asyncio.TimeoutError:
        LOGGER(__name__).error(f"[SHORT_URL] Request timed out for site: {site}")
        return None
    except Exception as e:
        LOGGER(__name__).error(f"[SHORT_URL] Unexpected error: {e}")
        return None


is_auth = filters.create(is_auth)
