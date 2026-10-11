from bot import app
from uvloop import install
from pyrogram import idle
import signal
import logging

install()

logger = logging.getLogger(__name__)

def _handle_signal(sig, frame):
    logger.info("Stop signal received (SIGTERM). Exiting...")
    raise SystemExit(0)

signal.signal(signal.SIGTERM, _handle_signal)

async def start():
    await app.start()

app.loop.run_until_complete(start())
idle()
