import asyncio
import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient
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
# =============================================================================

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

MESSAGES = ["muscular verse and topp here for chatting msgg me", "Hello"]


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
    print("No replies to DMs, tags, or trigger words - broadcast only.")
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
