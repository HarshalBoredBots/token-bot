from bot import app
from uvloop import install
import logging
import signal

install()

logger = logging.getLogger(__name__)

def _handle_signal(sig, frame):
    logger.info("Stop signal received (SIGTERM). Exiting...")
    app.loop.stop()

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)

async def start():
    await app.start()

app.loop.run_until_complete(start())
app.loop.run_forever()
