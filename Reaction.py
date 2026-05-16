import json
import os
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
)

SESSION_DIR = "TG_SESSIONS"
DB_FILE = "accounts.json"

os.makedirs(SESSION_DIR, exist_ok=True)


class SessionManager:
    def __init__(self):
        self.accounts = self.load_db()
        self.clients = {}

    # ---------- DATABASE ----------
    def load_db(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_db(self):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(
                self.accounts,
                f,
                indent=2,
                ensure_ascii=False
            )

    # ---------- ACCOUNT LIST ----------
    def show_accounts(self):
        print("\n=== ACCOUNT LIST ===")

        if not self.accounts:
            print("No accounts saved")
            return

        for i, acc in enumerate(self.accounts, 1):
            status = (
                "ACTIVE"
                if acc.get("active", True)
                else "INACTIVE"
            )

            phone = acc["phone"]
            masked = (
                f"{phone[:-4]}****"
                if len(phone) > 4
                else phone
            )

            print(
                f"[{i}] "
                f"{status} | "
                f"{masked} | "
                f"{acc['session']}"
            )

    # ---------- ADD ACCOUNT ----------
    async def add_account(self):
        print("\n=== ADD ACCOUNT ===")

        session_name = (
            f"acc{len(self.accounts)+1}"
        )

        acc = {
            "session": session_name,
            "api_id": int(
                input("API ID: ").strip()
            ),
            "api_hash": input(
                "API HASH: "
            ).strip(),
            "phone": input(
                "PHONE: "
            ).strip(),
            "active": True,
        }

        client = await self.login(acc)

        if client:
            self.accounts.append(acc)
            self.save_db()

            self.clients[
                session_name
            ] = client

            print(
                "\n✓ Account added"
            )

    # ---------- LOGIN ----------
    async def login(self, acc):
        session_path = os.path.join(
            SESSION_DIR,
            acc["session"]
        )

        client = TelegramClient(
            session_path,
            acc["api_id"],
            acc["api_hash"]
        )

        try:
            await client.connect()

            phone = acc["phone"]
            masked = phone[-4:]

            print(
                f"\nLoading: ****{masked}"
            )

            # already logged in
            if (
                await client.is_user_authorized()
            ):
                print(
                    "✓ Auto login success"
                )
                return client

            # first login only
            print(
                f"OTP required "
                f"(****{masked})"
            )

            await client.send_code_request(
                phone
            )

            code = input(
                f"OTP for ****{masked}: "
            ).strip()

            try:
                await client.sign_in(
                    phone,
                    code
                )

            except (
                SessionPasswordNeededError
            ):
                password = input(
                    "2FA Password: "
                ).strip()

                await client.sign_in(
                    password=password
                )

            print(
                "✓ Login successful"
            )

            return client

        except (
            PhoneCodeInvalidError
        ):
            print(
                "Invalid OTP"
            )

        except Exception as e:
            print(
                f"Login failed: {e}"
            )

        try:
            await client.disconnect()
        except Exception:
            pass

        return None

    # ---------- AUTO LOAD ----------
    async def load_all(self):
        active_accounts = [
            x for x in self.accounts
            if x.get("active", True)
        ]

        print(
            f"\nLoading "
            f"{len(active_accounts)} "
            f"active account(s)..."
        )

        for acc in active_accounts:
            client = await self.login(acc)

            if client:
                self.clients[
                    acc["session"]
                ] = client

    # ---------- SOFT LOGOUT ----------
    def disable_account(self):
        self.show_accounts()

        try:
            idx = (
                int(
                    input(
                        "\nSerial to disable: "
                    )
                ) - 1
            )

            if (
                idx < 0
                or idx >= len(self.accounts)
            ):
                print(
                    "Invalid serial"
                )
                return

            self.accounts[idx][
                "active"
            ] = False

            self.save_db()

            print(
                "✓ Account disabled "
                "(session kept)"
            )

        except Exception as e:
            print(
                f"Error: {e}"
            )

    # ---------- ENABLE ----------
    def enable_account(self):
        self.show_accounts()

        try:
            idx = (
                int(
                    input(
                        "\nSerial to enable: "
                    )
                ) - 1
            )

            if (
                idx < 0
                or idx >= len(self.accounts)
            ):
                print(
                    "Invalid serial"
                )
                return

            self.accounts[idx][
                "active"
            ] = True

            self.save_db()

            print(
                "✓ Account enabled "
                "(OTP not needed)"
            )

        except Exception as e:
            print(
                f"Error: {e}"
            )

    # ---------- CLEAN EXIT ----------
    async def shutdown(self):
        for client in (
            self.clients.values()
        ):
            try:
                await client.disconnect()
            except Exception:
                pass
