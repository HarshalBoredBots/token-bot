from var import _DYNAMIC, LOGGER
from bot import app as Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

scheduler = AsyncIOScheduler()
scheduler.start()


async def perform():
    """Rotate FSUB invite links on a schedule."""
    for channel, link in list(Bot.FSUB.items()):
        try:
            await Bot.revoke_chat_invite_link(channel, link)
        except Exception as e:
            LOGGER(__name__).warning(f"[fsub_timeout] Could not revoke link for {channel}: {e}")
        try:
            new_link       = await Bot.create_chat_invite_link(channel)
            Bot.FSUB[channel] = new_link.invite_link
        except Exception as e:
            LOGGER(__name__).warning(f"[fsub_timeout] Could not create new link for {channel}: {e}")
    LOGGER(__name__).info('Generated New FSUB Links')


# FIX 12: fsub_timeout and fsub_ids are read live at startup here.
# They are still frozen from the moment the module is imported — a /us change
# to FSUB_TIMEOUT only takes effect after a restart, which is now documented.
# The scheduler job is added once; restarting the bot re-evaluates the setting.
fsub_timeout = _DYNAMIC["FSUB_TIMEOUT"]()
fsub_ids     = _DYNAMIC["FSUB"]()

if fsub_timeout and fsub_ids:
    # Run once shortly after startup to rotate any stale links.
    scheduler.add_job(
        perform,
        'date',
        run_date=datetime.now() + timedelta(seconds=5),
    )
    # Then run on the configured interval.
    scheduler.add_job(
        perform,
        'interval',
        seconds=fsub_timeout,
    )
    LOGGER(__name__).info(
        f"[fsub_timeout] Link rotation scheduled every {fsub_timeout}s "
        f"for {len(fsub_ids)} FSUB channel(s). "
        f"Note: changing FSUB_TIMEOUT via /us requires a restart to take effect."
    )
