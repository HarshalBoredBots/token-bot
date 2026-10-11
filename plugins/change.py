from pyrogram import Client, filters
from var import *
from helper import *
import os
import sys
import aiohttp
import base64
import re
from urllib.parse import urlparse


async def update_github_file(repo_url: str, branch: str, file_name: str, new_content: str):
    parsed_url = urlparse(repo_url)
    match = re.search(r"ghp_\w+", parsed_url.netloc)
    if not match:
        LOGGER(__name__).error(
            "[change] UPSTREAM_REPO URL does not contain a GitHub PAT (ghp_...). "
            "Cannot push config update."
        )
        return False
    token = match.group(0)

    repo_path = parsed_url.path.strip("/").split("/")
    if len(repo_path) < 2:
        LOGGER(__name__).error("[change] Could not parse owner/repo from UPSTREAM_REPO URL.")
        return False
    repo_owner, repo_name = repo_path[0], repo_path[1]

    file_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_name}"
    headers  = {"Authorization": f"token {token}"}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(file_url, params={"ref": branch}) as response:
            if response.status != 200:
                LOGGER(__name__).error(f"[change] Error fetching file from GitHub: HTTP {response.status}")
                return False
            file_data = await response.json()
            file_sha  = file_data["sha"]

        new_content_encoded = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": f"Updating {file_name} via API",
            "content": new_content_encoded,
            "branch":  branch,
            "sha":     file_sha,
        }
        async with session.put(file_url, json=payload) as response:
            if response.status == 200:
                return True
            else:
                LOGGER(__name__).error(f"[change] Error updating file: HTTP {response.status}")
                return False


@Client.on_message(filters.private & filters.command('change'))
async def change(app, message):
    import var as _var
    if message.from_user.id not in _var.OWNER:
        return
    if not CURRENT_REPO or not CURRENT_BRANCH:
        return await replyMessage(message, '**Fill Up CURRENT_REPO & CURRENT_BRANCH First !**')
    try:
        key, value = [i.strip() for i in message.text.split(maxsplit=1)[1].strip().split('=', maxsplit=1)]
    except Exception:
        return await replyMessage(message, '**Send Correctly In Format Like `/change FSUB = "-100xx -100xx"`**')

    with open("config.env", "r") as file:
        lines = file.readlines()

    status = None
    with open("config.env", "w") as file:
        for line in lines:
            if line.split("=", maxsplit=1)[0].strip() == key:
                file.write(f"{key} = {value}\n")
                status = True
            else:
                file.write(line)

    if not status:
        return await replyMessage(message, '**`No Such Variable Found !`**')

    with open("config.env", "r") as file:
        lines = file.read()

    ok = await update_github_file(CURRENT_REPO, CURRENT_BRANCH, 'config.env', lines)
    if not ok:
        return await replyMessage(
            message,
            f'`Changed {key} locally but could not push to GitHub. '
            f'Check UPSTREAM_REPO contains a valid PAT and the bot has write access.`'
        )

    msg = await replyMessage(message, f'`Successfully Changed {key} = {value}, Now Restarting !`')
    with open(".restartmsg", "w") as f:
        f.write(f"{msg.chat.id}\n{msg.id}\n")
    # Use sys.exit on Heroku — os.execl does not work on Heroku's ephemeral filesystem.
    # Heroku will automatically restart the dyno after exit.
    sys.exit(0)
