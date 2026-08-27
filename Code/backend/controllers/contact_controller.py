"""
ContactController - xu ly 4 loai thong diep ket ban:
ADDFRIEND, FRIEND_RESP, FRIENDLIST, FRIENDREQUESTS.
"""

import socket

from Code.backend.services.contact_service import (
    get_friend_list, get_friend_requests, respond_friend_request,
    send_friend_request,
)
from Code.backend.utils.server_logger import log
from Code.config.server_config import ENCODING


class ContactController:
    def __init__(self, client_manager) -> None:
        self.client_manager = client_manager

    def handle(self, msg_type: str, content: str, username: str,
               client_socket: socket.socket) -> None:
        if msg_type == "ADDFRIEND":
            self._handle_add_friend(content, username, client_socket)
        elif msg_type == "FRIEND_RESP":
            self._handle_friend_resp(content, username, client_socket)
        elif msg_type == "FRIENDLIST":
            self._handle_friend_list(username, client_socket)
        elif msg_type == "FRIENDREQUESTS":
            self._handle_friend_requests(username, client_socket)

    def _handle_add_friend(self, content: str, username: str,
                            client_socket: socket.socket) -> None:
        target = content.strip()
        if not target:
            self._send(client_socket, "FRIENDREQ_ERR|Ten nguoi dung khong hop le.")
            return

        result = send_friend_request(username, target)
        if not result["ok"]:
            self._send(client_socket, f"FRIENDREQ_ERR|{result['error']}")
            return

        log(f"[ADDFRIEND] {username} -> {target}")
        self._send(client_socket, f"FRIENDREQ_OK|{target}")

        target_socket = self.client_manager.get_client(target)
        if target_socket is not None:
            self._send_safe(target_socket, f"FRIENDREQ_IN|{username}")

    def _handle_friend_resp(self, content: str, username: str,
                             client_socket: socket.socket) -> None:
        target, action = self._parse_pair(content)
        if target is None:
            self._send(client_socket, "FRIENDRESP_ERR|FRIEND_RESP dung dang: FRIEND_RESP|username|ACCEPT_hoac_REJECT")
            return

        accept = action.upper() == "ACCEPT"
        result = respond_friend_request(username, target, accept)
        if not result["ok"]:
            self._send(client_socket, f"FRIENDRESP_ERR|{result['error']}")
            return

        status_word = "ACCEPT" if accept else "REJECT"
        log(f"[FRIEND_RESP] {username} -> {target}: {status_word}")
        self._send(client_socket, f"FRIENDRESP_OK|{target}|{status_word}")

        requester_socket = self.client_manager.get_client(target)
        if requester_socket is not None:
            self._send_safe(requester_socket, f"FRIENDRESP_IN|{username}|{status_word}")

    def _handle_friend_list(self, username: str, client_socket: socket.socket) -> None:
        friends = get_friend_list(username)
        self._send(client_socket, f"FRIENDLIST|{','.join(friends)}")

    def _handle_friend_requests(self, username: str, client_socket: socket.socket) -> None:
        requests = get_friend_requests(username)
        self._send(client_socket, f"FRIENDREQUESTS|{','.join(requests)}")

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
    def _send(client_socket: socket.socket, message: str) -> None:
        client_socket.sendall((message + "\n").encode(ENCODING))

    @staticmethod
    def _send_safe(client_socket: socket.socket, message: str) -> None:
        try:
            client_socket.sendall((message + "\n").encode(ENCODING))
        except OSError:
            pass