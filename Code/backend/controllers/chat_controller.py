"""
ChatController - xu ly cac thong diep can LOGIN truoc: gui tin nhan
broadcast (MESSAGE), tin nhan rieng (PRIVATE), tra loi tin nhan
(REPLY), va chuyen tiep tin nhan (FORWARD). Cac thong diep private/
reply/forward deu duoc luu vao database qua chat_service.
"""

import socket

from Code.backend.services.chat_service import (
    get_message_brief, get_or_create_private_conversation, save_message,
)
from Code.backend.services.media_service import MediaError, save_image
from Code.backend.utils.server_logger import log
from Code.config.server_config import ENCODING


class ChatController:
    def __init__(self, client_manager, broadcaster, private_chat, get_user_id) -> None:
        self.client_manager = client_manager
        self.broadcaster = broadcaster
        self.private_chat = private_chat
        # callable(username) -> user_id | None, tro ve AuthController.user_ids
        self.get_user_id = get_user_id

    def handle(self, msg_type: str, content: str, username: str,
               client_socket: socket.socket) -> None:
        if msg_type == "MESSAGE":
            self._handle_message(content, username)
        elif msg_type == "PRIVATE":
            self._handle_private(content, username, client_socket)
        elif msg_type == "REPLY":
            self._handle_reply(content, username, client_socket)
        elif msg_type == "FORWARD":
            self._handle_forward(content, username, client_socket)
        elif msg_type == "IMAGE":
            self._handle_image(content, username, client_socket)

    # ------------------------------------------------------------------

    def _handle_message(self, content: str, username: str) -> None:
        log(f"[MESSAGE] {username}: {content}")
        self.broadcaster.broadcast(username, content)

    def _handle_private(self, content: str, username: str,
                         client_socket: socket.socket) -> None:
        receiver, message = self._parse_pair(content)
        if receiver is None:
            self._send(client_socket, "ERROR|PRIVATE dung dang: PRIVATE|NguoiNhan|NoiDung")
            return

        sender_id = self.get_user_id(username)
        receiver_id = self.get_user_id(receiver)
        message_id = None
        if sender_id and receiver_id:
            conv_id = get_or_create_private_conversation(sender_id, receiver_id)
            message_id = save_message(conv_id, sender_id, message)

        id_part = message_id if message_id is not None else 0
        message_with_id = f"{message}|{id_part}"

        if self.private_chat.send_private(username, receiver, message_with_id):
            if receiver != username:
                self._send(client_socket, f"PRIVATE|{username}|To {receiver}: {message}|{id_part}")
        else:
            self._send(client_socket, f"ERROR|Nguoi dung {receiver} khong online.")

    def _handle_reply(self, content: str, username: str,
                       client_socket: socket.socket) -> None:
        reply_to_id, reply_content = self._parse_reply(content)
        if reply_to_id is None:
            self._send(client_socket, "ERROR|REPLY dung dang: REPLY|message_id|noi_dung")
            return

        original = get_message_brief(reply_to_id)
        who = original["sender_display"] if original else ""
        snippet = original["content"] if original else ""

        log(f"[REPLY] {username} -> #{reply_to_id}: {reply_content}")
        packet = f"REPLY|{username}|{reply_content}|{reply_to_id}|{who}|{snippet}"
        for sock in self.client_manager.get_all_clients():
            self._send_safe(sock, packet)

    def _handle_forward(self, content: str, username: str,
                         client_socket: socket.socket) -> None:
        message_id, target_username = self._parse_forward(content)
        if message_id is None:
            self._send(client_socket, "ERROR|FORWARD dung dang: FORWARD|message_id|target_username")
            return

        original = get_message_brief(message_id)
        if original is None:
            self._send(client_socket, "ERROR|Tin nhan goc khong ton tai.")
            return

        sender_id = self.get_user_id(username)
        target_id = self.get_user_id(target_username)
        if sender_id and target_id:
            conv_id = get_or_create_private_conversation(sender_id, target_id)
            save_message(conv_id, sender_id, original["content"],
                         forward_from_message_id=message_id)

        if self.private_chat.send_private(username, target_username, original["content"]):
            log(f"[FORWARD] {username} -> {target_username}: #{message_id}")
        else:
            self._send(client_socket, f"ERROR|Nguoi dung {target_username} khong online.")

    def _handle_image(self, content: str, username: str,
                      client_socket: socket.socket) -> None:
        """Nhan IMAGE|target|filename|mime|base64 va chuyen anh toi client."""
        parts = content.split("|", 3)
        if len(parts) != 4:
            self._send(client_socket, "ERROR|IMAGE sai dinh dang.")
            return

        target, file_name, mime_type, data_base64 = parts
        target = target.strip()
        try:
            media = save_image(file_name, mime_type, data_base64)
        except MediaError as error:
            self._send(client_socket, f"ERROR|{error}")
            return

        packet = (
            f"IMAGE|{username}|{target}|{media['file_name']}|"
            f"{media['mime_type']}|{data_base64}"
        )

        if target == "__broadcast__":
            for sock in self.client_manager.get_all_clients():
                self._send_safe(sock, packet)
            log(f"[IMAGE] {username} -> tat ca: {media['file_name']}")
            return

        receiver_socket = self.client_manager.get_client(target)
        if receiver_socket is None:
            self._send(client_socket, f"ERROR|Nguoi dung {target} khong online.")
            return

        self._send_safe(receiver_socket, packet)
        if receiver_socket is not client_socket:
            self._send_safe(client_socket, packet)
        log(f"[IMAGE] {username} -> {target}: {media['file_name']}")

    # ------------------------------------------------------------------

    @staticmethod
    def _parse_pair(content: str):
        parts = content.split("|", 1)
        if len(parts) != 2:
            return None, None
        a, b = parts[0].strip(), parts[1].strip()
        if not a or not b:
            return None, None
        return a, b

    @staticmethod
    def _parse_reply(content: str):
        parts = content.split("|", 1)
        if len(parts) != 2:
            return None, None
        try:
            reply_to_id = int(parts[0].strip())
        except ValueError:
            return None, None
        return reply_to_id, parts[1].strip()

    @staticmethod
    def _parse_forward(content: str):
        parts = content.split("|", 1)
        if len(parts) != 2:
            return None, None
        try:
            message_id = int(parts[0].strip())
        except ValueError:
            return None, None
        return message_id, parts[1].strip()

    @staticmethod
    def _send(client_socket: socket.socket, message: str) -> None:
        client_socket.sendall((message + "\n").encode(ENCODING))

    @staticmethod
    def _send_safe(client_socket: socket.socket, message: str) -> None:
        try:
            client_socket.sendall((message + "\n").encode(ENCODING))
        except OSError:
            pass
