import os
import random
import re
import time
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ============================== CONFIG ======================================
# Railway par ye sab "Variables" tab me set karne hain (values file me mat likho)
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
STRING_SESSION = os.environ.get("STRING_SESSION", "")

GROUPS_ONLY = os.environ.get("GROUPS_ONLY", "true").lower() == "true"
COOLDOWN_SECONDS = int(os.environ.get("COOLDOWN_SECONDS", "1"))
# =============================================================================

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

ME_ID = None
ME_USERNAME = ""

# -----------------------------------------------------------------------------
# CATEGORIES: har category ke paas kai trigger phrases (synonyms) hote hain,
# jo sab ek hi reply-pool se match karte hain. Isse ~200 trigger phrases cover
# ho jate hain bina har ek ke liye alag reply pool likhe.
# -----------------------------------------------------------------------------

CATEGORIES = [
    ("hi", ["hi", "hii", "hiii", "hi hi", "heya"],
        ["Hii", "Hi hi", "Hello", "Hey", "Hi ji kaise ho", "Hi there",
         "Hey buddy", "Hi dost", "Hello bhai", "Hii kaise ho aap", "Heyy",
         "Hi kaisa chal raha hai sab", "Namaste", "Hi wassup"]),
    ("hello", ["hello", "hello ji", "hlo", "helo"],
        ["Hello", "Hello ji", "Hello there", "Hello bhai", "Hello dost",
         "Hello kaise ho", "Hey hello", "Hello g", "Hello kaise hain aap",
         "Hello sunn rahe ho", "Hello aap kaise hain", "Hola"]),
    ("hey", ["hey", "heyy", "heyyy"],
        ["Hey", "Heyy", "Hey there", "Hey dost", "Hey bhai", "Heyy kaise ho"]),
    ("yo", ["yo", "yoo"],
        ["Yo", "Yoo", "Yo bhai", "Yo kya haal"]),
    ("namaste", ["namaste", "namaskar"],
        ["Namaste", "Namaskar ji", "Namaste, kaise hain aap", "Namaste dost"]),
    ("salaam", ["salaam", "assalamualaikum"],
        ["Walaikum salaam", "Salaam bhai", "Salaam, kaise hain aap"]),
    ("hru", ["hru", "how r u", "how ru"],
        ["I'm fine yaar, tum batao", "Bas theek hu, tu bata", "All good bro, wbu",
         "Mast hu bhai, tu sunao", "I'm good, thanks for asking",
         "Sab badhiya, aap kaise ho", "Theek thaak, tum sunao",
         "I'm doing great, hru", "Chill kar raha hu, tu bata"]),
    ("how are you", ["how are you", "how are you doing", "kaise ho", "kaisi ho", "kaise ho aap"],
        ["I'm doing good, how about you?", "Main theek hu, aap kaise hain?",
         "All good here, wbu?", "Bas mast hu yaar, tu bata",
         "I'm fine, thanks! How are you?", "Sab sahi chal raha hai, tum batao",
         "Theek hu bhai, tum kaise ho", "Doing great, thanks for asking! HRU?",
         "Bindaas hu, tu sunao apna haal"]),
    ("wbu", ["wbu", "what about you"],
        ["I'm doing well too!", "Main bhi theek hu", "All good on my side too",
         "Same here, sab badhiya", "Bas chill kar raha hu", "I'm good too, thanks"]),
    ("wby", ["wby"],
        ["I'm good too!", "Main bhi mast hu", "Same yaar, sab badhiya hai",
         "All good here too"]),
    ("wassup", ["wassup", "whats up", "what's up", "sup"],
        ["Nothing much, tu bata", "Bas chill kar raha hu", "Kuch khaas nahi yaar",
         "All good, wassup with you", "Bas aise hi, tu bata apna",
         "Nothing new, sab normal hai"]),
    ("kya haal hai", ["kya haal hai", "kya haal chaal", "haal chaal"],
        ["Sab badhiya bhai", "Bas chal raha hai zindagi", "Mast hai sab kuch",
         "Thik thaak, tu bata apna haal", "Sab first class hai bhai"]),
    ("good morning", ["good morning", "gm", "subah bakhair"],
        ["Good morning", "Good morning ji", "Subah subah pyaar", "GM dost",
         "Good morning, have a nice day", "Morning morning",
         "Uth gaye aap bhi, good morning"]),
    ("good night", ["good night", "gn", "shubh ratri"],
        ["Good night", "GN dost", "Good night, sweet dreams", "Good night ji",
         "Achi neend aaye", "Good night, so jao ab", "Shubh ratri",
         "Good night, kal baat karte hai"]),
    ("good afternoon", ["good afternoon", "gud afternoon"],
        ["Good afternoon", "Afternoon ji", "Good afternoon, khana kha liya?",
         "Good afternoon dost"]),
    ("good evening", ["good evening", "gud evening"],
        ["Good evening", "Shaam badhiya ho", "Good evening ji",
         "Good evening dost, kaisa raha din"]),
    ("good day", ["good day", "have a good day"],
        ["Good day", "Aap bhi good day", "Have a great day", "Din badhiya rahe"]),
    ("bye", ["bye", "bye bye", "tata", "alvida"],
        ["Bye", "Bye bye", "Chalo bye, milte hai", "Bye take care", "Ok bye",
         "Bye dost", "Bye, phir baat karte hai"]),
    ("see you", ["see you", "cya", "see u"],
        ["See you", "Cya", "See you soon", "Milte hai phir"]),
    ("take care", ["take care", "khayal rakhna"],
        ["Take care", "Aap bhi take care", "Take care dost", "Khayal rakhna apna",
         "Aap bhi khayal rakhna"]),
    ("ok", ["ok", "okay", "k", "kk"],
        ["Ok", "Okay", "Ok theek hai", "Alright", "Ok noted", "Theek hai",
         "Ok samajh gaya", "Ok bhai"]),
    ("thik hai", ["thik hai", "theek hai", "thk h"],
        ["Thik hai", "Ok theek hai", "Chalo thik hai", "Theek hai bhai",
         "Haan thik hai", "Ok fine"]),
    ("kya kar rahe ho", ["kya kar rahe ho", "kya kar rhe ho", "kr kya rhe ho"],
        ["Bas relax kar raha hu, tu bata", "Kuch khaas nahi, tu bata apna",
         "Bas phone chala raha hu", "Kaam kar raha hu thoda",
         "Bas aise hi time pass", "Bas baithe hai, tu bata"]),
    ("kya kar rahi ho", ["kya kar rahi ho", "kya kr rhi ho"],
        ["Bas relax kar rahi hu, tu bata", "Kuch khaas nahi, tu bata apna",
         "Bas phone chala rahi hu", "Kaam kar rahi hu thoda"]),
    ("free ho kya", ["free ho kya", "free ho", "time hai kya"],
        ["Haan bilkul free hu, bolo", "Thoda busy hu, thodi der me free hoga",
         "Haan free hu, kya baat hai", "Free hi hu, tu bata"]),
    ("busy ho kya", ["busy ho kya", "busy ho", "kaam me ho kya"],
        ["Nahi free hu, bolo", "Thoda busy hu abhi, thodi der me baat karte hai",
         "Nahi yaar free hu, kya hua", "Bas thoda kaam hai, jaldi free ho jaunga"]),
    ("kaha ho", ["kaha ho", "kaha hai", "where are you", "kidhar ho"],
        ["Bas ghar par hu", "Bahar hu thoda kaam se", "Yahi hu, tu bata",
         "Ghar pe hi hu bhai", "Bas nearby hi hu"]),
    ("khana khaya", ["khana khaya", "khana kha liya", "lunch kiya", "dinner kiya"],
        ["Haan kha liya, tumne khaya?", "Abhi nahi khaya, tu bata",
         "Haan bhai kha liya", "Nahi abhi khana baaki hai", "Haan khaya, mast tha"]),
    ("so gaye kya", ["so gaye kya", "so gya kya", "sleeping"],
        ["Nahi abhi jaga hu", "Bas sone wala hu", "Nahi yaar abhi awake hu",
         "Thodi der me so jaunga"]),
    ("sona hai kya", ["sona hai kya", "neend aa rahi hai"],
        ["Haan thodi der me so jaunga", "Nahi abhi neend nahi hai",
         "Haan bahut neend aa rahi hai"]),
    ("uth gaye kya", ["uth gaye kya", "utha kya", "wake up"],
        ["Haan uth gaya", "Haan bhai jaga hu", "Uth gaye, good morning",
         "Haan abhi utha hu"]),
    ("miss you", ["miss you", "miss u", "yaad aa rahe ho"],
        ["Miss you too", "Aww miss you too yaar", "I miss you too dost",
         "Same here, bahut yaad aati hai"]),
    ("love you", ["love you", "love u", "ily"],
        ["Love you too", "Aww love you too", "I love you too yaar", "Same here dost"]),
    ("thank you", ["thank you", "thanku", "tysm"],
        ["Welcome", "Koi baat nahi", "You're welcome", "Anytime dost", "Welcome yaar"]),
    ("thanks", ["thanks", "thnx", "thx"],
        ["Welcome", "Koi baat nahi", "You're welcome", "Anytime bhai"]),
    ("sorry", ["sorry", "soory", "maaf karo"],
        ["Koi baat nahi", "It's ok yaar", "Arre sorry ki koi baat nahi",
         "No problem dost", "Chill kar, sab theek hai"]),
    ("welcome", ["welcome", "ur welcome", "most welcome"],
        ["Thank you", "Thanks dost", "Shukriya", "Thanks yaar"]),
    ("no problem", ["no problem", "np"],
        ["Great", "Thanks for understanding", "Ok cool"]),
    ("kya scene hai", ["kya scene hai", "scene kya hai"],
        ["Kuch khaas nahi, tu bata", "Bas chill scene hai", "Sab normal hai bhai"]),
    ("kya plan hai", ["kya plan hai", "plan kya hai"],
        ["Abhi kuch nahi socha, tu bata", "Kuch plan nahi hai abhi",
         "Batao kya karna hai"]),
    ("kal milte hai", ["kal milte hai", "kal baat karte hai"],
        ["Ok kal milte hai", "Done, kal baat karte hai", "Theek hai kal milna"]),
    ("good", ["good", "gud"],
        ["Nice", "Great", "Good hai", "Badhiya"]),
    ("nice", ["nice", "niceee"],
        ["Thanks", "Haan bilkul", "Right", "Sahi bola"]),
    ("cool", ["cool", "coool"],
        ["Haan bilkul cool", "Ekdum cool", "Yup", "Sahi hai"]),
    ("awesome", ["awesome", "osm"],
        ["Haan bilkul awesome", "Ekdum mast", "Sahi hai", "Great na"]),
    ("lol", ["lol", "lmao"],
        ["Haha lol", "Haha sach me", "Lol sahi hai"]),
    ("haha", ["haha", "hahaha", "hehe"],
        ["Haha", "Haha sahi hai", "Lol"]),
    ("really", ["really", "rly"],
        ["Haan sach me", "Bilkul really", "Haan yaar sach"]),
    ("sach me", ["sach me", "sachi"],
        ["Haan sach me", "Bilkul sach", "Haan yaar"]),
    ("accha", ["accha", "acha"],
        ["Haan accha hai", "Theek hai accha", "Haan sahi"]),
    ("long time no see", ["long time no see", "bahut din baad"],
        ["Haan bahut din baad, kaisa hai", "Sahi bola, kaha the itne din",
         "Haan yaar bahut time ho gaya"]),
    ("kaha the itne din", ["kaha the itne din", "kidhar the"],
        ["Bas busy tha thoda", "Kaam me tha yaar", "Bas aise hi time nahi mila"]),
    ("yaad aaya", ["yaad aaya", "yaad aayi"],
        ["Haan bahut yaad aaya", "Same here yaar", "Mujhe bhi yaad aata hai"]),
    ("good luck", ["good luck", "gud luck", "best of luck"],
        ["Thank you", "Thanks yaar", "Shukriya", "Thanks dost, dua karna"]),
    ("everything fine", ["everything fine", "all fine"],
        ["Haan sab fine hai", "Bilkul sab thik hai", "Haan sab badhiya"]),
    ("sab thik", ["sab thik", "sab theek", "everything ok"],
        ["Haan sab thik hai", "Bilkul sab badhiya", "Haan sab mast hai"]),
    ("congratulations", ["congratulations", "congrats", "cong"],
        ["Thank you so much", "Thanks yaar", "Shukriya dost"]),
    ("happy birthday", ["happy birthday", "hbd"],
        ["Thank you so much", "Thanks yaar, dua karna", "Shukriya dost"]),
    ("what happened", ["what happened", "kya hua", "kya ho gya"],
        ["Kuch nahi bas aise hi", "Sab thik hai, chinta na karo", "Bas thoda tired hu"]),
    ("good job", ["good job", "well done", "great job"],
        ["Thank you", "Thanks yaar", "Shukriya dost"]),
    ("kya bol raha hai", ["kya bol raha hai", "kya keh raha hai"],
        ["Sach keh raha hu yaar", "Bilkul sahi bol raha hu", "Haan sach me"]),
    ("pagal ho kya", ["pagal ho kya", "pagal hai kya"],
        ["Nahi yaar bilkul sahi hu", "Haha thoda pagal to hu", "Kyu kya hua"]),
    ("mast", ["mast", "mst"],
        ["Haan mast hai", "Bilkul mast", "Ekdum mast yaar"]),
    ("chalo", ["chalo", "chal"],
        ["Chalo", "Haan chalte hai", "Ok chalo", "Theek hai chalo"]),
    ("haan", ["haan", "han", "ha"],
        ["Haan", "Han ji", "Haan bilkul"]),
    ("nahi", ["nahi", "nhi", "na"],
        ["Nahi", "Nahi yaar", "Nahi bilkul nahi"]),
    ("kyu", ["kyu", "kyun", "why"],
        ["Bas aise hi", "Pata nahi yaar", "Kyu kya hua"]),
    ("kaise", ["kaise", "kese"],
        ["Aise hi", "Pata nahi kaise", "Bas ho gaya"]),
    ("kab", ["kab", "kb"],
        ["Jaldi hi", "Pata nahi abhi", "Bas thodi der me"]),
    ("kaun", ["kaun", "kon"],
        ["Main", "Pata nahi kaun", "Tu bata"]),
    ("kya", ["kya", "kia"],
        ["Kuch nahi", "Bas aise hi", "Bolo na"]),
    ("sahi hai", ["sahi hai", "sahi"],
        ["Haan sahi hai", "Bilkul sahi", "Sahi bola"]),
    ("galat hai", ["galat hai", "galat"],
        ["Nahi galat nahi hai", "Haan thoda galat hai"]),
    ("acha laga", ["acha laga", "accha laga"],
        ["Mujhe bhi acha laga", "Great to hear", "Nice yaar"]),
    ("bura laga", ["bura laga", "bura"],
        ["Sorry yaar", "Koi baat nahi", "Sab thik ho jayega"]),
    ("mazaak", ["mazaak", "joke"],
        ["Haha mazaak tha", "Just kidding yaar", "Haha sach me mazaak tha"]),
    ("sach", ["sach", "sacchi"],
        ["Haan sach hai", "Bilkul sach", "Sach me sach hai"]),
    ("jhooth", ["jhooth", "jhoot"],
        ["Nahi bilkul sach hai", "Jhooth kyu bologe", "Sach bol raha hu"]),
]

# Replies for when someone MENTIONS the userbot (@username) without a matching trigger
MENTION_REPLIES_BASE = [
    "Haan bolo?", "Ji bataye?", "Kise yaad kiya?", "Bulaya kisi ne?",
    "Haan main hu, bolo", "Kya baat hai bhai", "Ji sunn raha hu",
    "Bolo kya kaam hai", "Yes bolo", "Han bhai bolo",
]

# Replies for when someone REPLIES to the userbot's own previous message
REPLY_TO_ME_REPLIES_BASE = [
    "Haan bolo?", "Ji?", "Kya hua?", "Bolo na", "Sunn raha hu, bolo",
    "Haan kaho", "Ji bataye kya baat hai", "Haan bolte jao",
]

EMOJI_SUFFIXES = [
    "", "!", " 😊", " 🙂", " ✨", " 👍", " 😄", " 🤗", " 🔥", " ❤️", " 😁", " ✅",
]


def expand_pool(base_list):
    expanded = []
    for phrase in base_list:
        for suffix in EMOJI_SUFFIXES:
            expanded.append(f"{phrase}{suffix}".strip())
    return expanded


# Flatten: trigger phrase -> category name
TRIGGER_TO_CATEGORY = {}
CATEGORY_REPLIES = {}
for name, triggers, replies in CATEGORIES:
    CATEGORY_REPLIES[name] = expand_pool(replies)
    for t in triggers:
        TRIGGER_TO_CATEGORY[t] = name

SORTED_TRIGGERS = sorted(TRIGGER_TO_CATEGORY.keys(), key=len, reverse=True)

MENTION_REPLIES = expand_pool(MENTION_REPLIES_BASE)
REPLY_TO_ME_REPLIES = expand_pool(REPLY_TO_ME_REPLIES_BASE)

TOTAL_TRIGGER_PHRASES = len(TRIGGER_TO_CATEGORY)
TOTAL_REPLIES = sum(len(v) for v in CATEGORY_REPLIES.values()) + len(MENTION_REPLIES) + len(REPLY_TO_ME_REPLIES)

last_reply_time = {}  # chat_id -> last reply timestamp


def find_trigger_category(text: str):
    clean = re.sub(r"[^\w\s]", "", text.lower().strip())
    for trigger in SORTED_TRIGGERS:
        if clean == trigger or clean.startswith(trigger + " ") or f" {trigger} " in f" {clean} ":
            return TRIGGER_TO_CATEGORY[trigger]
    return None


def is_mentioned(text: str) -> bool:
    if not ME_USERNAME:
        return False
    return f"@{ME_USERNAME.lower()}" in text.lower()


@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if event.out:
        return

    # ---- ignore bots ----
    sender = await event.get_sender()
    if sender is None or getattr(sender, "bot", False):
        return

    if GROUPS_ONLY and not event.is_group:
        return

    text = event.raw_text or ""

    # ---- check reply-to-me ----
    replied_to_me = False
    if event.is_reply:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.sender_id == ME_ID:
            replied_to_me = True

    mentioned = is_mentioned(text)
    trigger_category = find_trigger_category(text)

    if not trigger_category and not mentioned and not replied_to_me:
        return

    # ---- cooldown ----
    chat_id = event.chat_id
    now = time.time()
    if chat_id in last_reply_time and now - last_reply_time[chat_id] < COOLDOWN_SECONDS:
        return
    last_reply_time[chat_id] = now

    if trigger_category:
        reply = random.choice(CATEGORY_REPLIES[trigger_category])
    elif mentioned:
        reply = random.choice(MENTION_REPLIES)
    else:
        reply = random.choice(REPLY_TO_ME_REPLIES)

    try:
        await event.reply(reply)
    except Exception as e:
        print(f"Reply failed in chat {chat_id}: {e}")


async def run():
    global ME_ID, ME_USERNAME
    await client.start()
    me = await client.get_me()
    ME_ID = me.id
    ME_USERNAME = me.username or ""
    print(f"Logged in as {me.first_name} (@{ME_USERNAME or 'no-username'})")
    print(f"Loaded {TOTAL_TRIGGER_PHRASES} trigger phrases, {TOTAL_REPLIES} total reply variations.")
    print("Mentions aur reply-to-me bhi enabled hain. Bots ignore honge.")
    print("Userbot is running. Press Ctrl+C to stop.")
    await client.run_until_disconnected()


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
