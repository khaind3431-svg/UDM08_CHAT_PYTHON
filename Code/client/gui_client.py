"""
GUI Client - nhung giao dien HTML/CSS/JS co san (Code/frontend) thanh
mot cua so desktop that bang pywebview, va noi no toi server TCP that
qua ChatApi.

Trinh duyet/JS thuan khong the tu mo TCP socket, nen toan bo phan ket
noi mang (LOGIN, REGISTER, MESSAGE, PRIVATE, REPLY, FORWARD, PING,
LOGOUT) duoc xu ly ben Python trong lop ChatApi, va duoc pywebview
"expose" sang cho JS goi qua window.pywebview.api.<ten_ham>(...).

Chieu nguoc lai (server gui du lieu ve), ChatApi day tung dong nhan
duoc sang cho JS bang cach goi ham JS toan cuc window.onServerMessage(line)
(dinh nghia trong Code/frontend/js/network.js).

Cach chay:
    python Code/client/gui_client.py
"""

import json
import socket
import sys
import threading
from pathlib import Path
from typing import Optional

import webview

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
LOGIN_PAGE = str(FRONTEND_DIR / "login.html")
CHAT_PAGE = str(FRONTEND_DIR / "chat.html")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
ENCODING = "utf-8"


class ChatApi:
    """Lop duoc expose sang JS qua js_api. Moi ham public o day co the
    duoc goi tu JS bang: window.pywebview.api.ten_ham(...) -> Promise."""

    def __init__(self) -> None:
        self.window: Optional["webview.Window"] = None
        self.sock: Optional[socket.socket] = None
        self.connected = False
        self.username: Optional[str] = None
        self.display_name: Optional[str] = None
        self.online_users: list[str] = []

    def set_window(self, window: "webview.Window") -> None:
        self.window = window

    def connect(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict:
        if self.connected:
            return {"ok": True}
        try:
            self.sock = socket.create_connection((host, port), timeout=5)
        except OSError as error:
            return {"ok": False, "error": f"Khong ket noi duoc toi server ({host}:{port}): {error}"}

        self.connected = True
        threading.Thread(target=self._recv_loop, daemon=True).start()
        return {"ok": True}

    def _recv_loop(self) -> None:
        buffer = ""
        sock = self.sock
        while self.connected and sock is not None:
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
        self.connected = False
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
    webview.start(debug="--debug" in sys.argv)


if __name__ == "__main__":
    main()