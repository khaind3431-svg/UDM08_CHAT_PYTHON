import json
import os
import socket
import sys
import threading
from pathlib import Path
from typing import Optional

import webview

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
LOGIN_PAGE = str(FRONTEND_DIR / "login.html")
CHAT_PAGE = str(FRONTEND_DIR / "chat.html")

STORAGE_PATH = str(Path.home() / ".wireline_chat" / f"gui-{os.getpid()}")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
ENCODING = "utf-8"


class ChatApi:
    def __init__(self) -> None:
        self.window: Optional["webview.Window"] = None
        self.sock: Optional[socket.socket] = None
        self.connected = False
        self.username: Optional[str] = None
        self.display_name: Optional[str] = None
        self.online_users: list[str] = []
        self._lock = threading.Lock()
        self._generation = 0

    def set_window(self, window: "webview.Window") -> None:
        self.window = window

    def connect(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
        with self._lock:
            if self.connected:
                return {"ok": True}
            try:
                new_sock = socket.create_connection((host, port), timeout=5)
            except OSError as error:
                return {"ok": False, "error": f"Khong ket noi duoc toi server ({host}:{port}): {error}"}

            new_sock.settimeout(None)

            if self.sock is not None:
                try:
                    self.sock.close()
                except OSError:
                    pass

            self._generation += 1
            my_generation = self._generation
            self.sock = new_sock
            self.connected = True

        threading.Thread(target=self._recv_loop, args=(my_generation, new_sock), daemon=True).start()
        return {"ok": True}

    def _recv_loop(self, my_generation: int, sock: socket.socket) -> None:
        buffer = ""
        while self.connected and self._generation == my_generation:
            try:
                data = sock.recv(4096)
            except OSError:
                break
            if not data:
                break
            buffer += data.decode(ENCODING, errors="replace")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if line:
                    self._handle_incoming_line(line)

        if self._generation == my_generation:
            self.connected = False
            self._push_to_js("__DISCONNECTED__")

    def _handle_incoming_line(self, line: str) -> None:
        if line.startswith("ONLINE|"):
            payload = line.split("|", 1)[1]
            self.online_users = [u for u in payload.split(",") if u]
        self._push_to_js(line)

    def _push_to_js(self, line: str) -> None:
        window = self.window
        if window is None:
            return
        try:
            window.evaluate_js(f"window.onServerMessage({json.dumps(line)})")
        except Exception:
            pass

    def _send_raw(self, message: str) -> dict:
        if not self.connected or self.sock is None:
            return {"ok": False, "error": "Chua ket noi toi server."}
        try:
            self.sock.sendall((message + "\n").encode(ENCODING))
            return {"ok": True}
        except OSError as error:
            self.connected = False
            return {"ok": False, "error": str(error)}

    def login(self, username: str, password: str) -> dict:
        result = self.connect()
        if not result["ok"]:
            return result
        self.username = username
        return self._send_raw(f"LOGIN|{username}|{password}")

    def register(self, display_name: str, username: str, password: str, confirm: str) -> dict:
        result = self.connect()
        if not result["ok"]:
            return result
        return self._send_raw(f"REGISTER|{display_name}|{username}|{password}|{confirm}")

    def send_message(self, content: str) -> dict:
        return self._send_raw(f"MESSAGE|{content}")

    def send_private(self, receiver: str, content: str) -> dict:
        return self._send_raw(f"PRIVATE|{receiver}|{content}")

    def send_reply(self, reply_to_id, content: str) -> dict:
        return self._send_raw(f"REPLY|{reply_to_id}|{content}")

    def send_forward(self, message_id, target_username: str) -> dict:
        return self._send_raw(f"FORWARD|{message_id}|{target_username}")

    def ping(self) -> dict:
        return self._send_raw("PING")

    def logout(self) -> dict:
        result = self._send_raw("LOGOUT")
        with self._lock:
            self.connected = False
            self._generation += 1
            if self.sock is not None:
                try:
                    self.sock.close()
                except OSError:
                    pass
            self.sock = None
        self.username = None
        self.online_users = []
        return result

    def get_state(self) -> dict:
        return {
            "username": self.username,
            "connected": self.connected,
            "online_users": self.online_users,
        }

    def navigate_to_chat(self) -> None:
        if self.window is not None:
            self.window.load_url(CHAT_PAGE)

    def navigate_to_login(self) -> None:
        if self.window is not None:
            self.window.load_url(LOGIN_PAGE)


def main() -> None:
    api = ChatApi()
    window = webview.create_window(
        "Wireline - Chat TCP",
        LOGIN_PAGE,
        js_api=api,
        width=1180,
        height=760,
        min_size=(960, 600),
    )
    api.set_window(window)
    os.makedirs(STORAGE_PATH, exist_ok=True)
    webview.start(debug="--debug" in sys.argv, storage_path=STORAGE_PATH)


if __name__ == "__main__":
    main()