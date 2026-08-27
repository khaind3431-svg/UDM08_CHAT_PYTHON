"""
ProfileController - xu ly thong diep GETINFO: tra ve thong tin ca nhan
(ho ten, bio, trang thai, quan he ket ban) cua 1 user cho nguoi xem.
"""

import socket

from Code.backend.services import profile_service
from Code.config.server_config import ENCODING


class ProfileController:
    def __init__(self, get_user_id) -> None:
        # callable(username) -> user_id | None (tro toi AuthController.user_ids)
        self.get_user_id = get_user_id

    def handle(self, msg_type: str, content: str, username: str,
               client_socket: socket.socket) -> None:
        if msg_type == "GETINFO":
            self._handle_get_info(content, username, client_socket)

    def _handle_get_info(self, content: str, username: str,
                          client_socket: socket.socket) -> None:
        target_username = content.strip()
        viewer_id = self.get_user_id(username)
        if viewer_id is None:
            self._send(client_socket, "ERROR|Phien dang nhap khong hop le.")
            return

        result = profile_service.get_user_profile(username, viewer_id, target_username)
        if not result["ok"]:
            self._send(client_socket, f"ERROR|{result['error']}")
            return

        profile = result["profile"]
        # "|" va xuong dong trong bio/full_name se pha vo dinh dang dong
        # (client tach cac truong bang "|"), nen thay the truoc khi gui.
        full_name = self._sanitize(profile["full_name"])
        bio = self._sanitize(profile["bio"])

        self._send(
            client_socket,
            f"USERINFO|{profile['username']}|{full_name}|{bio}|"
            f"{profile['status']}|{profile['friend_status']}",
        )

    @staticmethod
    def _sanitize(text: str) -> str:
        return text.replace("|", "/").replace("\n", " ").replace("\r", " ")

    @staticmethod
    def _send(client_socket: socket.socket, message: str) -> None:
        client_socket.sendall((message + "\n").encode(ENCODING))