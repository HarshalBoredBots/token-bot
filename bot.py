from aiohttp import web
from plugins import web_server
from pyrogram import Client
import sys
from datetime import datetime
from var import *
import os


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=API_ID,
            plugins={"root": "plugins"},
            workers=5,
            bot_token=BOT_TOKEN,
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        self.username = (await self.get_me()).username
        self.uptime = datetime.now()

        from var import _DYNAMIC
        channel_id = _DYNAMIC["CHANNEL_ID"]()
        fsub_ids   = _DYNAMIC["FSUB"]()
        fsub_links = _DYNAMIC["FSUB_LINKS"]()
        toggle     = _DYNAMIC["TOGGLE"]()
        req_fsub   = _DYNAMIC["REQUEST_FSUB"]()
        session    = _DYNAMIC["SESSION"]()

        try:
            self.db_channel = await self.get_chat(channel_id)
            test = await self.send_message(chat_id=channel_id, text=".")
            await test.delete()
        except Exception as e:
            self.LOGGER(__name__).warning(f"Check DB Channel! Error: {e}")
            self.LOGGER(__name__).info("\nBot Stopped !")
            sys.exit()

        self.LOGGER(__name__).info("Bot Running..!")

        async def generate_invite_link(ids):
            try:
                link = (await self.get_chat(ids)).invite_link
                if not link:
                    await self.export_chat_invite_link(ids)
                    link = (await self.get_chat(ids)).invite_link
                return link
            except Exception as e:
                self.LOGGER(__name__).warning(
                    f"Could not get invite link for FSUB channel {ids}: {e} "
                    f"— make sure the bot is admin there. Skipping this channel."
                )
                return None

        # Normal FSUB
        self.FSUB = {}
        for index, ids in enumerate(fsub_ids):
            if not fsub_links:
                link = await generate_invite_link(ids)
            else:
                link = fsub_links[index]
            if link:
                self.FSUB[ids] = link

        # Request FSUB
        if toggle and session:
            user = Client(
                "user",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=session,
                no_updates=True,
            )
            await user.start()
            self.PENDING = {}
            for ids in req_fsub:
                self.PENDING[ids] = []
                link = await generate_invite_link(ids)
                if not link:
                    continue
                try:
                    await user.get_chat(ids)
                except Exception:
                    await user.join_chat(link)
                lst = []
                async for user_ in user.get_chat_join_requests(ids):
                    lst.append(user_.user.id)
                self.PENDING[ids] = lst

        if os.path.exists(".restartmsg"):
            with open(".restartmsg") as f:
                chat_id, msg_id = map(int, f)
                try:
                    await self.edit_message_text(
                        chat_id=chat_id, message_id=msg_id, text="`Restarted !`"
                    )
                    os.remove(".restartmsg")
                except Exception:
                    pass

        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")


# FIX 1: Use a distinct name for the instance so it doesn't shadow the class.
# Previously: Bot = Bot() followed by `from bot import Bot` in main.py
# re-imported the CLASS over the instance, destroying it.
app = Bot()
