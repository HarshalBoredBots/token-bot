from pyrogram import Client, filters
from var import LOGGER
from settings_db import as_bool, as_id_list


@Client.on_chat_join_request()
async def request_fsub(app, message):
    # Read live from DB so /us changes apply after restart
    if not as_bool("TOGGLE"):
        return
    req_fsub_ids = as_id_list("REQUEST_FSUB")
    if message.chat.id not in req_fsub_ids:
        return
    pending = getattr(app, "PENDING", {})
    if message.chat.id not in pending:
        pending[message.chat.id] = []
    if message.from_user.id not in pending[message.chat.id]:
        pending[message.chat.id].append(message.from_user.id)
    LOGGER(__name__).info(f"Synced {message.from_user.id} In Requests !")
