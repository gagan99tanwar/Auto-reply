import asyncio
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ============================== CONFIG ======================================

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

INTERVAL_SECONDS = int(os.environ.get("INTERVAL_SECONDS", "300"))  # 5 minutes
START_HOUR = int(os.environ.get("START_HOUR", "7"))
END_HOUR = int(os.environ.get("END_HOUR", "23"))
TIMEZONE = os.environ.get("TIMEZONE", "Asia/Kolkata")
GAP_BETWEEN_GROUPS = float(os.environ.get("GAP_BETWEEN_GROUPS", "2"))

# Put your own image in the project folder with this name.
PHOTO_PATH = os.environ.get("PHOTO_PATH", "photo.jpg")

# The link used in the DM flow.
DM_LINK = os.environ.get(
    "DM_LINK",
    "https://t.me/P77Game_bot?start=ref7321525865",
)

# ============================== DM FLOW =====================================

DM_STEPS = {
    0: "hello 🤗",
    1: "Koi mera channel join karega\nApnii bubu dikha dungiii😁😁🤭🤭",
    2: DM_LINK,
    3: "Start karo fir channel aaega join kro",
    4: "__PHOTO__",
    5: "Phle join kro fir bubu dikhaungi free me😘😘",
    6: "Screenshot dikhao",
}

DM_STATE_FILE = "dm_state.json"


def load_dm_state():
    try:
        with open(DM_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {str(k): int(v) for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
        return {}


def save_dm_state(state):
    try:
        with open(DM_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Could not save {DM_STATE_FILE}: {e}")


dm_state = load_dm_state()


async def send_dm_step(event, user_id):
    """Send the next DM step and advance the user's state."""
    key = str(user_id)
    step = dm_state.get(key, 0)

    # Flow is complete; don't restart it on later messages.
    if step >= len(DM_STEPS):
        return

    content = DM_STEPS[step]

    try:
        if content == "__PHOTO__":
            if os.path.isfile(PHOTO_PATH):
                await client.send_file(event.chat_id, PHOTO_PATH)
            else:
                print(
                    f"Photo not found: {PHOTO_PATH}. "
                    "Add photo.jpg to the project folder or set PHOTO_PATH."
                )
                # If the photo is unavailable, still continue the flow.
        else:
            await client.send_message(event.chat_id, content)

        dm_state[key] = step + 1
        save_dm_state(dm_state)
        print(f"DM step {step} sent to user {user_id}.")
    except Exception as e:
        print(f"DM step {step} failed for user {user_id}: {e}")


@client.on(events.NewMessage(incoming=True))
async def dm_handler(event):
    if event.out or not event.is_private:
        return

    sender = await event.get_sender()

    if sender is None or getattr(sender, "bot", False):
        return

    user_id = sender.id
    current_step = dm_state.get(str(user_id), 0)

    # First incoming DM -> hello.
    # Every later incoming text advances the flow by one step.
    await send_dm_step(event, user_id)

    # Steps 2 and 3 are sent automatically one after another.
    # After the link, send the follow-up text immediately, then the photo.
    if current_step == 2:
        await send_dm_step(event, user_id)
        await send_dm_step(event, user_id)

    elif current_step == 3:
        await send_dm_step(event, user_id)


# ============================== GROUP FLOW ==================================

GROUP_MESSAGES = [
    "hii kese ho",
    "Hru aao na",
    "Acha g",
    "Me achi larki hun",
    "Dedo na",
]

group_message_index = 0


def is_within_active_hours() -> bool:
    now = datetime.now(ZoneInfo(TIMEZONE))
    return START_HOUR <= now.hour < END_HOUR


async def get_authorized_group_ids():
    """
    Use GROUP_IDS to explicitly choose groups where the bot may post.

    Example:
        GROUP_IDS=-1001234567890,-1009876543210

    If GROUP_IDS is empty, no group broadcast is performed.
    """
    raw = os.environ.get("GROUP_IDS", "").strip()

    if not raw:
        return []

    group_ids = []
    for value in raw.split(","):
        value = value.strip()
        if not value:
            continue
        try:
            group_ids.append(int(value))
        except ValueError:
            print(f"Invalid GROUP_IDS value ignored: {value}")

    return group_ids


async def broadcast_once():
    global group_message_index

    groups = await get_authorized_group_ids()

    if not groups:
        print("No GROUP_IDS configured; skipping group broadcast.")
        return

    message = GROUP_MESSAGES[group_message_index]
    group_message_index = (group_message_index + 1) % len(GROUP_MESSAGES)

    sent = 0

    for chat_id in groups:
        try:
            await client.send_message(chat_id, message)
            sent += 1
        except Exception as e:
            print(f"Failed to send to group {chat_id}: {e}")

        await asyncio.sleep(GAP_BETWEEN_GROUPS)

    print(f"Sent '{message}' to {sent}/{len(groups)} authorized groups.")


async def broadcast_loop():
    while True:
        if is_within_active_hours():
            await broadcast_once()
        else:
            now = datetime.now(ZoneInfo(TIMEZONE))
            print(
                f"Outside active hours "
                f"({now.strftime('%H:%M')} {TIMEZONE}), "
                "skipping this cycle."
            )

        await asyncio.sleep(INTERVAL_SECONDS)


# ============================== RUN =========================================

async def run():
    await client.start()

    me = await client.get_me()

    print(f"Logged in as {me.first_name}")
    print(
        f"Group messages rotate every {INTERVAL_SECONDS}s "
        f"between {START_HOUR}:00 and {END_HOUR}:00 ({TIMEZONE})."
    )
    print("DM flow enabled.")
    print(f"Photo path: {PHOTO_PATH}")

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
        print(
            f"Missing environment variables: {', '.join(missing)}"
        )
        print(
            "Railway Variables me API_ID, API_HASH aur STRING_SESSION set karein."
        )
    else:
        client = TelegramClient(
            StringSession(STRING_SESSION),
            API_ID,
            API_HASH,
        )

        print("Userbot starting...")
        client.loop.run_until_complete(run())
