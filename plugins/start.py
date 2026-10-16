from pyrogram import Client, filters
from var import *
from helper import *
from db import *
from datetime import datetime
import asyncio
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

# FIX 6: Module-level broadcast lock — prevents two concurrent /broadcast runs
# from racing over users_list simultaneously.
_broadcasting = False


@Client.on_message(filters.command(['start']))
async def start(app, message):
    await add_user(message.from_user.id)

    # FIX 7: BAN check enforced at entry — banned users are rejected immediately.
    if message.from_user.id in cf.get('BAN', []):
        return await replyMessage(message, "<b>You are banned from using this bot.</b>")

    stat, returned = await check_fsubs(app, message.from_user.id)
    if stat:
        text = f'''<b>Hello {message.from_user.mention}\n\nYou need to join in my Channel(s) to use me\n\nKindly Please join below channel(s).</b>'''
        try:
            returned.append(
                [InlineKeyboardButton('Try Again', url=f"https://t.me/{app.username}?start={message.command[1]}")]
            )
        except Exception:
            pass
        return await replyMessage(message, text, reply_markup=InlineKeyboardMarkup(returned))

    text = message.text
    if len(text.split()) == 1:
        text = f'''<b>Hello {message.from_user.mention}\n        \nI can store private files in Specified Channel and other users can access it from special link.\nDo /help To Know More ❤️</b>'''
        return await replyMessage(message, text, reply_markup=None)

    temp = await replyMessage(message, '<b>Please Wait ...</b>', reply_markup=None)

    from var import _DYNAMIC
    SHORTENER         = _DYNAMIC["SHORTENER"]()
    SHORTENER_PREMIUM = _DYNAMIC["SHORTENER_PREMIUM"]()
    HOW_TO_DOWNLOAD   = _DYNAMIC["HOW_TO_DOWNLOAD"]()
    PREMIUM_LINK      = _DYNAMIC["PREMIUM_LINK"]()
    CUSTOM_CAPTION    = _DYNAMIC["CUSTOM_CAPTION"]()
    AUTO_DELETE       = _DYNAMIC["AUTO_DELETE"]()
    PROTECT           = _DYNAMIC["PROTECT"]()
    CHANNEL_ID        = _DYNAMIC["CHANNEL_ID"]()

    if SHORTENER and not text.split()[1].startswith('code-'):
        if not (SHORTENER_PREMIUM and prem_dict['PREMIUM'].get(str(message.from_user.id))):
            text_ = '''**👋 ʜᴇʏ ᴛʜᴇʀᴇ\n\n• Your Movie / Series Link is Ready to Watch or Download\n\n✅  Kɪɴᴅʟʏ Cʟɪᴄᴋ ᴏɴ Dᴏᴡɴʟᴏᴀᴅ Bᴜᴛᴛᴏɴ 👇**'''
            temper = 'code-' + (await encoder(text.split(maxsplit=1)[1], app.username))
            original_url = f"https://telegram.me/{app.username}?start={temper}"

            short_link = await short_url(original_url)
            if not short_link or not isinstance(short_link, str) or not short_link.startswith("http"):
                short_link = original_url

            # Download button (top row, full width)
            reply_markup = [[InlineKeyboardButton("• ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ •", url=short_link)]]

            # Premium + Tutorial (second row, side by side when both are set)
            second_row = []
            if PREMIUM_LINK and isinstance(PREMIUM_LINK, str) and PREMIUM_LINK.startswith("http"):
                second_row.append(InlineKeyboardButton("ᴘʀᴇᴍɪᴜᴍ", url=PREMIUM_LINK))
            if HOW_TO_DOWNLOAD and isinstance(HOW_TO_DOWNLOAD, str) and HOW_TO_DOWNLOAD.startswith("http"):
                second_row.append(InlineKeyboardButton("ᴛᴜᴛᴏʀɪᴀʟ", url=HOW_TO_DOWNLOAD))
            if second_row:
                reply_markup.append(second_row)

            await replyMessage(message, text_, reply_markup=InlineKeyboardMarkup(reply_markup))
            return await temp.delete()

    if text.split()[1].startswith('code-'):
        text = text.split()[0] + " " + (await decoder(text.split()[1].split('-', 1)[1], app.username))

    try:
        base64_string = text.split()[1]
    except IndexError:
        return await temp.delete()
    try:
        string = await decode(base64_string)
    except Exception:
        return await temp.delete()

    argument = string.split('-')
    if argument[0] == 'get':
        ids = await get_old_format(argument)
    else:
        if len(argument) == 1:
            ids = [int(string)]
        else:
            ids = range(int(argument[0]), int(argument[1]) + 1)
    if not ids:
        return await temp.delete()

    # FIX 15: Replaced bare except with except Exception for proper error handling.
    try:
        messages = await asyncio.gather(*[app.get_messages(CHANNEL_ID, x) for x in ids])
        messages = [mg for mg in messages if not mg.empty]
    except Exception as e:
        LOGGER(__name__).error(f"get_messages failed: {e}")
        await replyMessage(message, "<b>Something went wrong..!</b>")
        return await temp.delete()

    to_delete = []
    for msg in messages:
        # FIX 6 (caption): Guard against non-file media types where .document
        # and .video are both None, which would raise AttributeError on .file_name.
        if msg.document or msg.video:
            filename         = (msg.document or msg.video).file_name
            filesize         = (msg.document or msg.video).file_size
            previouscaption  = msg.caption or ""
            caption = CUSTOM_CAPTION.format(
                filename=filename,
                filesize=filesize,
                previouscaption=previouscaption,
            ) if CUSTOM_CAPTION else None
            f_msg = await copyMessage(msg, message.chat.id, caption=caption, protect=PROTECT)
        else:
            f_msg = await copyMessage(msg, message.chat.id, protect=PROTECT)
        to_delete.append(f_msg)

    if AUTO_DELETE:
        to_delete.append(message)
        delete_msg = await replyMessage(
            message,
            f'<b>These Message Would Be Deleted In {await get_readable_time(AUTO_DELETE)}, So Save Them Somewhere Else !</b>'
        )
        to_delete.append(delete_msg)

        # FIX 3: asyncio.gather MUST be awaited or the coroutine is created
        # but never executed — messages would silently never be deleted.
        async def clean_messages(delay, _list):
            await asyncio.sleep(delay)
            await asyncio.gather(*[deleteMessage(m) for m in _list])

        asyncio.get_event_loop().create_task(clean_messages(AUTO_DELETE, to_delete))

    await temp.delete()


@Client.on_message(filters.private & filters.command('broadcast'))
async def send_text(client, message):
    global _broadcasting
    import var as _var
    if message.from_user.id not in _var.OWNER:
        return

    if not message.reply_to_message:
        # FIX 8: removed pointless msg = assignment for the reply.
        await message.reply("`Reply To A Message !`")
        return

    # FIX 6: Guard against concurrent broadcasts.
    if _broadcasting:
        return await replyMessage(message, "<b>A broadcast is already in progress. Please wait.</b>")

    _broadcasting = True
    broadcast_msg = message.reply_to_message

    total       = 0
    successful  = 0
    blocked     = 0
    deleted     = 0
    unsuccessful = 0

    stats_text = """<b><u>Broadcast {status}</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""

    pls_wait = await replyMessage(message, "<i>Broadcasting Message.. This will Take Some Time</i>")

    # FIX 2: Iterate over a snapshot copy of users_list so that del_user()
    # removing entries mid-iteration does not cause users to be skipped.
    # FIX 4: Exclude banned users from the broadcast.
    banned = set(cf.get('BAN', []))
    query  = get_users_snapshot()

    try:
        for chat_id in query:
            if chat_id in banned:
                total += 1
                continue
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value * 1.5)
                # FIX 1: Retry is now wrapped in its own try/except so a second
                # FloodWait or any other error does NOT abort the entire loop.
                try:
                    await broadcast_msg.copy(chat_id)
                    successful += 1
                except Exception:
                    unsuccessful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except Exception:
                unsuccessful += 1

            total += 1

            # FIX 3: Proactive inter-message delay (~20 msg/sec) avoids
            # hammering Telegram and accumulating FloodWait penalties.
            await asyncio.sleep(0.05)

            # FIX 5: Update status every 20 users (not 5) to reduce
            # editMessage calls on large userbases.
            if total % 20 == 0:
                try:
                    await pls_wait.edit(stats_text.format(
                        status="Processing",
                        total=total, successful=successful,
                        blocked=blocked, deleted=deleted,
                        unsuccessful=unsuccessful,
                    ))
                except Exception:
                    pass
    finally:
        # FIX 7: Use try/finally so the status message is always cleaned up
        # and final stats are always sent, even if an exception occurs mid-loop.
        _broadcasting = False
        await pls_wait.delete()

    await replyMessage(
        message,
        stats_text.format(
            status="Completed",
            total=total, successful=successful,
            blocked=blocked, deleted=deleted,
            unsuccessful=unsuccessful,
        )
    )


@Client.on_message(filters.command('stats') & is_auth)
async def stats(bot, message):
    now   = datetime.now()
    delta = now - bot.uptime
    time  = await get_readable_time(delta.seconds)
    await replyMessage(message, f"<b>BOT UPTIME\n{time}</b>")


@Client.on_message(filters.command('users') & is_auth)
async def users(bot, message):
    await replyMessage(message, f"<b>Total {len(users_list)} users are using this bot !</b>")


@Client.on_message(filters.command('log') & is_auth)
async def log(bot, message):
    await message.reply_document('log.txt', caption='<b>Log File</b>', quote=True)


@Client.on_message(filters.command('ban') & is_auth)
async def ban_(bot, message):
    try:
        user_id = int(message.text.split(maxsplit=1)[1])
        if 'BAN' not in cf:
            cf['BAN'] = []
        if user_id not in cf['BAN']:
            cf['BAN'].append(user_id)
            await message.reply_text(f'**Banned {user_id}**', True)
            return await sync()
        await message.reply_text(f'**Already Banned {user_id}**', True)
        await sync()
    except Exception:
        return await message.reply_text('**Send Correct User ID**', True)


@Client.on_message(filters.command('unban') & is_auth)
async def unban_(bot, message):
    try:
        user_id = int(message.text.split(maxsplit=1)[1])
        if 'BAN' not in cf:
            cf['BAN'] = []
        if user_id in cf['BAN']:
            cf['BAN'].remove(user_id)
            await message.reply_text(f'**UnBanned {user_id}**', True)
            return await sync()
        await message.reply_text(f'**Not Banned {user_id}**', True)
        await sync()
    except Exception:
        return await message.reply_text('**Send Correct User ID**', True)


@Client.on_message(filters.command('banlist') & is_auth)
async def banlist_(bot, message):
    text = message.text.split(maxsplit=1)
    if len(text) > 1:
        user_id = text[1]
        return await message.reply_text(
            f"**{user_id} Ban Status : {'Banned' if user_id in cf.get('BAN', []) else 'Not Banned'}**", True
        )
    await message.reply_text(f"**Total Banned Users : {len(cf.get('BAN', []))}**", True)


@Client.on_message(filters.command('help') & filters.private & is_auth)
async def help_cmd(app, message):
    text = """<b>Help Menu

/start - Start the bot
/help - Show this menu

<u>Admin Commands:</u>
/stats - Bot uptime
/users - Total user count
/log - Get log file
/ban [user_id] - Ban a user
/unban [user_id] - Unban a user
/banlist - List banned users
/broadcast - Broadcast a message (reply to it)
/batch - Start a batch upload
/done - Finish batch upload
/batchx - Create batch link interactively
/us - Open settings panel

<u>Owner Commands:</u>
/change KEY = VALUE - Update config
/addpremium [user_id] [expiry] - Add premium user
/removepremium [user_id] - Remove premium user
/listpremium - List premium users</b>"""
    await replyMessage(message, text)
