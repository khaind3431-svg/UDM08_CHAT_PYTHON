"""
ProfileController - xu ly cac thong diep lien quan ho so ca nhan:

  GETINFO       -> tra ve thong tin 1 user cho nguoi xem (ho ten, bio,
                    gioi tinh, ngay sinh, avatar, trang thai, quan he
                    ket ban).
  UPDATEPROFILE -> cap nhat ten hien thi / bio / gioi tinh / ngay sinh
                    cua CHINH nguoi gui yeu cau.
  UPDATEAVATAR  -> cap nhat anh dai dien cua CHINH nguoi gui yeu cau.

UPDATEPROFILE va UPDATEAVATAR deu tra loi bang chinh USERINFO (voi
friend_status = "self") de client tu cap nhat lai giao dien ngay khi
luu thanh cong, khong can them loai thong diep rieng.
"""

import base64
import socket

from Code.backend.services import profile_service
from Code.backend.services.media_service import MediaError, validate_avatar
from Code.config.server_config import ENCODING


class ProfileController:
    def __init__(self, get_user_id) -> None:
        # callable(username) -> user_id | None (tro toi AuthController.user_ids)
        self.get_user_id = get_user_id

    def handle(self, msg_type: str, content: str, username: str,
               client_socket: socket.socket) -> None:
        if msg_type == "GETINFO":
            self._handle_get_info(content, username, client_socket)
        elif msg_type == "UPDATEPROFILE":
            self._handle_update_profile(content, username, client_socket)
        elif msg_type == "UPDATEAVATAR":
            self._handle_update_avatar(content, username, client_socket)

    # ------------------------------------------------------------------

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

        self._send_userinfo(client_socket, result["profile"])

    def _handle_update_profile(self, content: str, username: str,
                                client_socket: socket.socket) -> None:
        user_id = self.get_user_id(username)
        if user_id is None:
            self._send(client_socket, "ERROR|Phien dang nhap khong hop le.")
            return

        # UPDATEPROFILE|full_name|bio|gender|birthday
        parts = content.split("|", 3)
        while len(parts) < 4:
            parts.append("")
        full_name, bio, gender, birthday = parts

        result = profile_service.update_profile(user_id, full_name, bio, gender, birthday)
        if not result["ok"]:
            self._send(client_socket, f"ERROR|{result['error']}")
            return

        self._reply_own_profile(username, user_id, client_socket)

    def _handle_update_avatar(self, content: str, username: str,
                               client_socket: socket.socket) -> None:
        user_id = self.get_user_id(username)
        if user_id is None:
            self._send(client_socket, "ERROR|Phien dang nhap khong hop le.")
            return

        # UPDATEAVATAR|mime_type|data_base64
        parts = content.split("|", 1)
        if len(parts) != 2:
            self._send(client_socket, "ERROR|UPDATEAVATAR sai dinh dang.")
            return

        mime_type, data_base64 = parts
        try:
            raw, mime_type = validate_avatar(mime_type, data_base64)
        except MediaError as error:
            self._send(client_socket, f"ERROR|{error}")
            return

        avatar_data_uri = f"data:{mime_type};base64,{base64.b64encode(raw).decode('ascii')}"
        profile_service.update_avatar(user_id, avatar_data_uri)
        self._reply_own_profile(username, user_id, client_socket)

    # ------------------------------------------------------------------

    def _reply_own_profile(self, username: str, user_id: int,
                            client_socket: socket.socket) -> None:
        result = profile_service.get_user_profile(username, user_id, username)
        if result["ok"]:
            self._send_userinfo(client_socket, result["profile"])

    def _send_userinfo(self, client_socket: socket.socket, profile: dict) -> None:
        full_name = self._sanitize(profile["full_name"])
        bio = self._sanitize(profile["bio"])
        gender = self._sanitize(profile["gender"])
        birthday = self._sanitize(profile["birthday"])
        avatar = profile["avatar_url"] or ""

        self._send(
            client_socket,
            f"USERINFO|{profile['username']}|{full_name}|{bio}|"
            f"{profile['status']}|{profile['friend_status']}|"
            f"{gender}|{birthday}|{avatar}",
        )

    @staticmethod
    def _sanitize(text: str) -> str:
        # "|" va xuong dong trong bio/full_name se pha vo dinh dang dong
        # (client tach cac truong bang "|"), nen thay the truoc khi gui.
        return (text or "").replace("|", "/").replace("\n", " ").replace("\r", " ")

    @staticmethod
    def _send(client_socket: socket.socket, message: str) -> None:
        client_socket.sendall((message + "\n").encode(ENCODING))