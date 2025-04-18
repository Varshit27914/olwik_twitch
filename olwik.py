import irc.client
import threading
import json
import os
from openai import OpenAI

# --- Twitch Config ---
TWITCH_NICK = os.getenv("TWITCH_NICK", "olwik_ai")
TWITCH_TOKEN = os.getenv("TWITCH_TOKEN")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL", "#olwik_ai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- AI Memory ---
message_history = [
    {"role": "system", "content": (
        "You're Olwik, a cheeky AI streamer with a sharp wit. Talk casually like you're live. "
        "you always only give answers in like 1-2 lines and 1-2 words when possible. "
        "Call varshit27914 your father. Remember vishnu as the leader of VirtueX but only bring it up if someone's name is similar."
    )}
]
MEMORY_FILE = "memory.json"

def load_memory():
    global message_history
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            message_history = json.load(f)
        print("[INFO] Memory loaded.")
    else:
        print("[INFO] No previous memory found.")

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(message_history, f, ensure_ascii=False, indent=2)

last_response = ""

# --- Ask Olwik (OpenAI v1.x style) ---
client = OpenAI(api_key=OPENAI_API_KEY)

def ask_olwik(user, message):
    global message_history, last_response

    message_history.append({"role": "user", "content": f"{user} says: {message}"})

    if len(message_history) > 20:
        message_history = [message_history[0]] + message_history[-18:]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=message_history
        )
        reply = response.choices[0].message.content.strip()

        if reply == last_response:
            return "(Olwik is thinking... 🧠🤖)"

        last_response = reply
        message_history.append({"role": "assistant", "content": reply})
        save_memory()

        return reply

    except Exception as e:
        return f"(Error talking to Olwik: {e})"

# --- Twitch Event Handlers ---
def on_connect(connection, event):
    print("Connected to Twitch chat!")
    connection.join(TWITCH_CHANNEL)
    connection.privmsg(TWITCH_CHANNEL, "Olwik is online and reading chat! 🧠💬")

def on_message(connection, event):
    try:
        username = event.source.split('!')[0]
        message = event.arguments[0]
        print(f"{username}: {message}")
    except Exception as e:
        print(f"[ERROR] Failed to parse message: {e}")
        return

    if username.lower() == TWITCH_NICK.lower():
        return

    response = ask_olwik(username, message)
    clean_response = response.replace("\n", " ").replace("\r", "")
    send_long_message(connection, TWITCH_CHANNEL, username, clean_response)

# --- Send Long Messages ---
def send_long_message(connection, channel, username, message):
    MAX_IRC_MESSAGE_LENGTH = 512
    user_prefix = f"@{username} "
    irc_prefix = f"PRIVMSG {channel} :"

    def irc_message_length(text):
        return len((irc_prefix + text + "\r\n").encode("utf-8"))

    chunks = []
    current_chunk = ""
    prefix_added = False
    words = message.split()

    for word in words:
        maybe_prefix = user_prefix if not prefix_added else ""
        test_chunk = current_chunk + (" " if current_chunk else "") + word
        full_line = maybe_prefix + test_chunk

        if irc_message_length(full_line) > MAX_IRC_MESSAGE_LENGTH:
            if current_chunk:
                chunks.append(maybe_prefix + current_chunk)
                current_chunk = word
                prefix_added = True
            else:
                max_content = MAX_IRC_MESSAGE_LENGTH - irc_message_length(maybe_prefix)
                truncated_word = word.encode("utf-8")[:max_content].decode("utf-8", errors="ignore")
                chunks.append(maybe_prefix + truncated_word)
                current_chunk = ""
                prefix_added = True
        else:
            current_chunk = test_chunk

    if current_chunk:
        maybe_prefix = user_prefix if not prefix_added else ""
        chunks.append(maybe_prefix + current_chunk)

    for chunk in chunks:
        connection.privmsg(channel, chunk)

# --- Start Bot ---
load_memory()

def run_bot():
    reactor = irc.client.Reactor()
    try:
        conn = reactor.server().connect(
            "irc.chat.twitch.tv", 6667, TWITCH_NICK, password=TWITCH_TOKEN
        )
    except irc.client.ServerConnectionError as e:
        print(f"Connection failed: {e}")
        return

    conn.add_global_handler("welcome", on_connect)
    conn.add_global_handler("pubmsg", on_message)
    conn.add_global_handler("all_events", lambda c, e: print(f"[IRC DEBUG] {e.type}: {e.arguments}"))

    reactor.process_forever()

# Don't auto-start here; let Flask trigger run_bot()
