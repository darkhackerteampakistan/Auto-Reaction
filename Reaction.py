import asyncio
import json
import os
import random

from telethon import TelegramClient, functions
from telethon.tl.types import ReactionEmoji
from telethon.errors import SessionPasswordNeededError

# ---------------- STORAGE PATH AUTO DETECT ----------------

POSSIBLE_PATHS = [
    "/storage/emulated/0/AUTO_REACTION",
    os.path.expanduser("~/AUTO_REACTION"),
]

BASE_DIR = None

for path in POSSIBLE_PATHS:
    if os.path.exists(path):
        BASE_DIR = path
        break

if not BASE_DIR:
    BASE_DIR = "/storage/emulated/0/AUTO_REACTION"

SESSION_DIR = os.path.join(BASE_DIR, "TG_SESSIONS")
DB_FILE = os.path.join(BASE_DIR, "accounts.json")

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(BASE_DIR, exist_ok=True)

print("Storage path:", BASE_DIR)

# ---------------- GLOBALS ----------------

clients = []
accounts = []

REACTIONS = ["👍", "❤️", "🔥", "😂", "😮"]

# ---------------- DB ----------------

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return []


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------- LINK PARSE ----------------

def parse_link(link):
    link = link.replace("https://t.me/", "").replace("http://t.me/", "").strip("/")
    parts = link.split("/")
    return parts[-2], int(parts[-1])


# ---------------- LOGIN ----------------

async def login_account(i, acc):
    session_path = os.path.join(SESSION_DIR, acc["session"])

    client = TelegramClient(
        session_path,
        acc["api_id"],
        acc["api_hash"]
    )

    await client.connect()

    phone = acc["phone"]
    masked = phone[-4:]

    print("\n----------------------------")
    print(f"ACCOUNT {i}")
    print(f"PHONE: ****{masked}")
    print("----------------------------")

    if not await client.is_user_authorized():
        print("First login → OTP required")

        await client.send_code_request(phone)
        code = input(f"OTP for ****{masked}: ").strip()

        try:
            await client.sign_in(phone, code)

        except SessionPasswordNeededError:
            pwd = input(f"2FA Password for ****{masked}: ").strip()
            await client.sign_in(password=pwd)

        print("Login success → session saved")

    else:
        print("Session found → auto login (NO OTP)")

    return client


# ---------------- LOAD ALL ----------------

async def load_all():
    global accounts

    accounts = load_db()

    if not accounts:
        print("No accounts found")
        return

    print(f"\nLoading {len(accounts)} accounts...\n")

    for i, acc in enumerate(accounts, 1):
        if not acc.get("active", True):
            print(f"Skipping inactive account {i}")
            continue

        try:
            client = await login_account(i, acc)
            clients.append(client)
        except Exception as e:
            print(f"Account {i} failed:", e)


# ---------------- ADD ACCOUNT ----------------

async def add_account():
    print("\n=== ADD ACCOUNT ===")

    acc = {
        "session": f"acc{len(accounts)+1}",
        "api_id": int(input("API ID: ")),
        "api_hash": input("API HASH: ").strip(),
        "phone": input("PHONE: ").strip(),
        "active": True
    }

    accounts.append(acc)
    save_db(accounts)

    client = await login_account(len(accounts), acc)
    clients.append(client)


# ---------------- SHOW ----------------

def show_accounts():
    print("\n=== ACCOUNT LIST ===")

    if not accounts:
        print("No accounts found")
        return

    for i, acc in enumerate(accounts, 1):
        status = "ACTIVE" if acc.get("active", True) else "INACTIVE"
        print(f"[{i}] {status} | {acc['phone']} | {acc['session']}")


# ---------------- LOGOUT (SOFT) ----------------

def logout_account():
    show_accounts()

    try:
        idx = int(input("\nEnter serial to logout: ")) - 1

        if 0 <= idx < len(accounts):
            accounts[idx]["active"] = False
            save_db(accounts)
            print("✔ Logged out (session kept)")
        else:
            print("Invalid selection")

    except Exception as e:
        print("Error:", e)


# ---------------- ENABLE ----------------

def enable_account():
    show_accounts()

    try:
        idx = int(input("\nEnter serial to enable: ")) - 1

        if 0 <= idx < len(accounts):
            accounts[idx]["active"] = True
            save_db(accounts)
            print("✔ Enabled")
        else:
            print("Invalid selection")

    except Exception as e:
        print("Error:", e)


# ---------------- REACTION ----------------

async def send_reaction(client, chat, msg_id):
    emoji = random.choice(REACTIONS)

    try:
        await client(functions.messages.SendReactionRequest(
            peer=chat,
            msg_id=msg_id,
            reaction=[ReactionEmoji(emoticon=emoji)]
        ))
        print("Reaction sent:", emoji)

    except Exception as e:
        print("Failed:", e)


# ---------------- REACT ALL ----------------

async def react_all(link):
    chat, msg_id = parse_link(link)

    print("\n=== SENDING REACTIONS ===")

    for i, client in enumerate(clients, 1):
        try:
            await client.connect()

            print(f"ACCOUNT {i}")
            await send_reaction(client, chat, msg_id)

            await asyncio.sleep(random.randint(3, 6))

        except Exception as e:
            print(f"Account {i} skipped:", e)


# ---------------- MAIN ----------------

async def main():
    await load_all()

    while True:
        print("""
====================
1. Add Account
2. Show Accounts
3. Logout Account
4. Enable Account
5. Send Reaction
6. Exit
====================
""")

        choice = input("Choose: ").strip()

        if choice == "1":
            await add_account()

        elif choice == "2":
            show_accounts()

        elif choice == "3":
            logout_account()

        elif choice == "4":
            enable_account()

        elif choice == "5":
            link = input("Post link: ").strip()
            await react_all(link)

        else:
            break

    for c in clients:
        await c.disconnect()


asyncio.run(main())
