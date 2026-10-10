from bot import app
from uvloop import install
from pyrogram import idle

install()

async def start():
    await app.start()

# FIX 2: Removed Bot.loop.run_forever() which blocked forever, making
# idle() unreachable dead code. The correct Pyrogram pattern is:
# run_until_complete(start()) to launch, then idle() to keep alive.
app.loop.run_until_complete(start())
idle()
