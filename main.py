import asyncio
import json
import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ============================== CONFIG ======================================
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

INTERVAL_SECONDS = int(os.environ.get("INTERVAL_SECONDS", "300"))  # 5 minutes
START_HOUR = int(os.environ.get("START_HOUR", "7"))    # 7 AM
END_HOUR = int(os.environ.get("END_HOUR", "23"))       # 11 PM
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Kolkata")  # server ka time zone alag ho sakta hai
GAP_BETWEEN_GROUPS = float(os.environ.get("GAP_BETWEEN_GROUPS", "2"))  # seconds, rate-limit se bachne ke liye

# ---- DM auto-reply: group link + caption ----
GC_LINK = os.environ.get("GC_LINK", "https://t.me/+0cKdhqQU4p84ZmQ1")
GC_CAPTION = os.environ.get("GC_CAPTION", "Join gays chatting group 🫠🫠❤️❤️💘")
DM_SENT_FILE = os.environ.get("DM_SENT_FILE", "dm_sent_users.json")
# =============================================================================

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

MESSAGES = ["Hiii muscularr guyy here for friendshipp", "hello handsomee toppp versee heree msgg for chattingg"]


def load_dm_sent():
    try:
        with open(DM_SENT_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_dm_sent(sent_set):
    try:
        with open(DM_SENT_FILE, "w") as f:
            json.dump(list(sent_set), f)
    except Exception as e:
        print(f"Could not save {DM_SENT_FILE}: {e}")


dm_sent_users = load_dm_sent()


@client.on(events.NewMessage(incoming=True))
async def dm_handler(event):
    if event.out or not event.is_private:
        return

    sender = await event.get_sender()
    if sender is None or getattr(sender, "bot", False):
        return

    if sender.id in dm_sent_users:
        return  # already sent once to this user, never again

    dm_sent_users.add(sender.id)
    save_dm_sent(dm_sent_users)

    try:
        await client.send_message(event.chat_id, GC_LINK)
        await asyncio.sleep(1)
        await client.send_message(event.chat_id, GC_CAPTION)
    except Exception as e:
        print(f"DM reply failed for user {sender.id}: {e}")


def is_within_active_hours() -> bool:
    now = datetime.now(ZoneInfo(TIMEZONE))
    return START_HOUR <= now.hour < END_HOUR


async def get_all_group_ids():
    group_ids = []
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            group_ids.append(dialog.id)
    return group_ids


async def broadcast_once():
    groups = await get_all_group_ids()
    message = random.choice(MESSAGES)
    sent = 0
    for chat_id in groups:
        try:
            await client.send_message(chat_id, message)
            sent += 1
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")
        await asyncio.sleep(GAP_BETWEEN_GROUPS)
    print(f"Sent '{message}' to {sent}/{len(groups)} groups.")


async def broadcast_loop():
    while True:
        if is_within_active_hours():
            await broadcast_once()
        else:
            now = datetime.now(ZoneInfo(TIMEZONE))
            print(f"Outside active hours ({now.strftime('%H:%M')} {TIMEZONE}), skipping this cycle.")
        await asyncio.sleep(INTERVAL_SECONDS)


async def run():
    await client.start()
    me = await client.get_me()
    print(f"Logged in as {me.first_name}")
    print(f"Broadcasting every {INTERVAL_SECONDS}s to all groups, "
          f"between {START_HOUR}:00 and {END_HOUR}:00 ({TIMEZONE}).")
    print("DM's ka reply group-link ke saath jayega. Tag/trigger words pe koi reply nahi.")
    await broadcast_loop()


if __name__ == "__main__":
    missing = []
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not STRING_SESSION.strip():
        missing.append("STRING_SESSION")

    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        print("Railway par 'Variables' tab me API_ID, API_HASH, STRING_SESSION set karein.")
        print("STRING_SESSION generate karne ke liye apne computer par generate_session.py chalayein.")
    else:
        print("Userbot starting...")
        client.loop.run_until_complete(run())
