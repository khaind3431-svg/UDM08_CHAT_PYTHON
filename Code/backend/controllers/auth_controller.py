"""
AuthController - xu ly 2 loai thong diep LOGIN va REGISTER: xac thuc
tai khoan, dang ky username moi, cap nhat trang thai online/offline,
va thong bao cho cac client khac khi co nguoi vao/roi phong chat.
"""

import socket

from Code.backend.services.auth_service import (
    authenticate_user, register_user, set_user_status,
)
from Code.backend.utils.server_logger import log
from Code.config.server_config import ENCODING


class AuthController:
    def __init__(self, client_manager, online_manager, broadcaster) -> None:
        self.client_manager = client_manager
        self.online_manager = online_manager
        self.broadcaster = broadcaster
        # username -> user.id (database). ChatController can gia tri nay
        # de luu tin nhan, nen ChatServer se doc qua thuoc tinh user_ids.
        self.user_ids: dict[str, int] = {}

    def handle(self, msg_type: str, content: str, client_socket: socket.socket,
               client_address) -> "str | None":
        """Tra ve username neu LOGIN thanh cong, nguoc lai None."""
        if msg_type == "LOGIN":
            return self._handle_login(content, client_socket, client_address)
        if msg_type == "REGISTER":
            self._handle_register(content, client_socket)
            return None
        return None

    def handle_disconnect(self, username: "str | None", client_socket: socket.socket) -> None:
        """Goi khi mot client (da tung LOGIN) ngat ket noi."""
        if username is None:
            return
        self.client_manager.unregister_username(username, client_socket)
        user_id = self.user_ids.pop(username, None)
        if user_id:
            set_user_status(user_id, "offline")
        self.broadcaster.broadcast("SYSTEM", f"{username} da roi phong chat.")
        self.online_manager.send_online_list()

    # ------------------------------------------------------------------

    def _handle_login(self, content: str, client_socket: socket.socket,
                       client_address) -> "str | None":
        username, password = self._parse_login(content)
        if username is None:
            self._send(client_socket, "ERROR|LOGIN dung dang: LOGIN|username|password")
            return None

        auth_result = authenticate_user(username, password)
        if not auth_result["ok"]:
            self._send(client_socket, f"LOGIN_ERR|{auth_result['error']}")
            return None

        if not self.client_manager.register_username(username, client_socket):
            self._send(client_socket, "LOGIN_ERR|Tai khoan dang dang nhap noi khac.")
            return None

        self.user_ids[username] = auth_result["user"]["id"]
        set_user_status(auth_result["user"]["id"], "online")

        log(f"{username} dang nhap tu {client_address[0]}:{client_address[1]}")
        self._send(client_socket, f"LOGIN_OK|{username}|{auth_result['user']['full_name']}")
        self.online_manager.send_online_list()
        self.broadcaster.broadcast("SYSTEM", f"{username} da tham gia phong chat.")
        return username

    def _handle_register(self, content: str, client_socket: socket.socket) -> None:
        parts = content.split("|", 3)
        if len(parts) != 4:
            self._send(client_socket, "REGISTER_ERR|Dinh dang khong hop le.")
            return

        display_name, username, password, confirm = (p.strip() for p in parts)
        result = register_user(display_name, username, password, confirm)
        if result["ok"]:
            self._send(client_socket, "REGISTER_OK")
        else:
            self._send(client_socket, f"REGISTER_ERR|{result['error']}")

    @staticmethod
    def _parse_login(content: str):
        parts = content.split("|", 1)
        if len(parts) != 2:
            return None, None
        username, password = parts[0].strip(), parts[1].strip()
        if not username or not password:
            return None, None
        return username, password

    @staticmethod
    def _send(client_socket: socket.socket, message: str) -> None:
        client_socket.sendall((message + "\n").encode(ENCODING))