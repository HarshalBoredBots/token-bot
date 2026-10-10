from pyrogram import Client, filters
from bot import app as Bot
from var import *
from helper import *
from db import *
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
from .fsub_timeout import scheduler
from apscheduler.triggers.date import DateTrigger
from settings_db import as_bool

id_to_task = {}


async def restart_jobs():
    shortener_premium = as_bool("SHORTENER_PREMIUM")
    shortener         = as_bool("SHORTENER")
    if not (shortener_premium and shortener):
        return
    copy_data = {k: v for k, v in prem_dict['PREMIUM'].items()}
    now = datetime.now(TIME_ZONE)
    for k, v in copy_data.items():
        schedule_time = max(v['END'], now + relativedelta(seconds=10))
        end_task = scheduler.add_job(
            premium_over,
            DateTrigger(run_date=schedule_time, timezone=TIME_ZONE),
            args=[int(k)],
        )
        id_to_task[int(k)] = end_task.id

# FIX 1 (premium.py): Use the instance `app`, not the class `Bot`.
# Previously `from bot import Bot` imported the class after the instance was
# re-assigned, so Bot.loop was the class attribute, not the running loop.
Bot.loop.create_task(restart_jobs())


async def premium_over(user_id):
    del prem_dict['PREMIUM'][str(user_id)]
    await prem_sync()
    try:
        await Bot.send_message(
            user_id,
            "**Your Premium Subscription Has Expired Today, Please Pay Again To Admin Continue**"
        )
    except Exception:
        pass
    LOGGER(__name__).info(f'Premium Over For {user_id}')


async def calc_end(now: datetime, expiry: str):
    try:
        num  = int(expiry[:-1])
        unit = expiry[-1]
        deltas = {
            'h': relativedelta(hours=num),
            'd': relativedelta(days=num),
            'w': relativedelta(weeks=num),
            'm': relativedelta(months=num),
            'y': relativedelta(years=num),
            's': relativedelta(seconds=num),
        }
        delta = deltas.get(unit)
        if delta is None:
            return None
        return now + delta
    except (ValueError, TypeError):
        return None


@Client.on_message(filters.command("addpremium"))
async def addpremium(app, message):
    import var as _var
    if message.from_user.id not in _var.OWNER:
        return
    shortener_premium = as_bool("SHORTENER_PREMIUM")
    shortener         = as_bool("SHORTENER")
    if not (shortener_premium and shortener):
        return await replyMessage(message, '`PREMIUM MODE IS OFF, TURN IT ON FIRST`')
    try:
        user_id, expiry = message.text.split()[1:]
        user_id   = int(user_id)
        user_chat = await app.get_chat(user_id)
    except Exception:
        return await replyMessage(
            message,
            '`Make Sure To Provide In This Format` : `/addpremium user_id expiry`\n\n'
            '`Supported Expiry Format - h (hours), d (days), w (weeks), m (months), y (years)`\n\n'
            '`Also Make Sure User Has Started The Bot !!!`'
        )

    # FIX 11: Validate expiry BEFORE calling calc_end, not after.
    # Original code called calc_end(now, expiry) first, then checked `if not expiry`.
    if not expiry:
        return await replyMessage(
            message,
            '`Provide Correct Expiry ! Supported Format - h (hours), d (days), w (weeks), m (months), y (years)`'
        )

    now = datetime.now(TIME_ZONE)
    end = await calc_end(now, expiry)
    if end is None:
        return await replyMessage(
            message,
            '`Invalid expiry format. Supported: h (hours), d (days), w (weeks), m (months), y (years)`'
        )

    if str(user_id) in prem_dict['PREMIUM']:
        return await replyMessage(message, '`User Already Premium`')

    prem_dict['PREMIUM'][str(user_id)] = {}
    prem_dict['PREMIUM'][str(user_id)]['NAME'] = (
        user_chat.first_name + " " + (user_chat.last_name or "")
    ).strip()
    prem_dict['PREMIUM'][str(user_id)]['END'] = end

    await replyMessage(
        message,
        f'`{prem_dict["PREMIUM"][str(user_id)]["NAME"]} Added, '
        f'Will Be Removed On {await readable_datetime(prem_dict["PREMIUM"][str(user_id)]["END"])}`'
    )
    end_task = scheduler.add_job(
        premium_over,
        DateTrigger(run_date=end, timezone=TIME_ZONE),
        args=[user_id],
    )
    id_to_task[user_id] = end_task.id
    try:
        await app.send_message(
            user_id,
            f"**You Have Been Added To Premium List, Now You Won't See Any Ads\n\n"
            f"Your Premium End Date Is: {await readable_datetime(end)}**"
        )
    except Exception:
        pass
    await prem_sync()


async def kill_task(user_id):
    if user_id in id_to_task:
        scheduler.remove_job(id_to_task[user_id])
        del id_to_task[user_id]


@Client.on_message(filters.command("removepremium"))
async def removepremium(app, message):
    import var as _var
    if message.from_user.id not in _var.OWNER:
        return
    shortener_premium = as_bool("SHORTENER_PREMIUM")
    shortener         = as_bool("SHORTENER")
    if not (shortener_premium and shortener):
        return await replyMessage(message, '`PREMIUM MODE IS OFF, TURN IT ON FIRST`')
    try:
        user_id = int(message.text.split(maxsplit=1)[1])
    except Exception:
        return await replyMessage(message, '`Make Sure To Provide In This Format` : `/removepremium user_id`')
    if str(user_id) not in prem_dict['PREMIUM']:
        return await replyMessage(message, '`User Is Not A Premium User`')
    name = prem_dict['PREMIUM'][str(user_id)]['NAME']
    del prem_dict['PREMIUM'][str(user_id)]
    await replyMessage(message, f'`{name} Removed !`')
    await kill_task(user_id)
    await prem_sync()


@Client.on_message(filters.command("listpremium"))
async def listpremium(app, message):
    import var as _var
    if message.from_user.id not in _var.OWNER:
        return
    shortener_premium = as_bool("SHORTENER_PREMIUM")
    shortener         = as_bool("SHORTENER")
    if not (shortener_premium and shortener):
        return await replyMessage(message, '`PREMIUM MODE IS OFF, TURN IT ON FIRST`')
    if not prem_dict['PREMIUM']:
        return await replyMessage(message, '`No Premium Users Found`')
    string = "List Of Premium Users -\n\n"
    for count, (i, j) in enumerate(prem_dict['PREMIUM'].items(), 1):
        string += f"{count}. {j['NAME']} [{i}] - END ON {await readable_datetime(j['END'])}\n"
    if len(string.strip()) < 4096:
        return await replyMessage(message, f"`{string.strip()}`")
    with open('premium.txt', 'w', encoding='utf-8') as f:
        f.write(string.strip())
    await message.reply_document('premium.txt', caption='`Premium Users List`', quote=True)
    os.remove('premium.txt')
