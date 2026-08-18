"""
ClientManager - quan ly tap trung tat ca socket dang ket noi va anh xa
username <-> socket cua cac client dang online.

Day la noi duy nhat luu trang thai "ai dang online", duoc dung chung
boi Broadcaster, PrivateChat, OnlineManager, AuthController va
ClientHandler.
"""

import socket
import threading


class ClientManager:
    def __init__(self) -> None:
        # Tat ca socket dang ket noi, ke ca chua LOGIN xong.
        self._all_sockets: set[socket.socket] = set()
        # username -> socket, chi cac client da LOGIN thanh cong.
        self._sockets_by_username: dict[str, socket.socket] = {}
        self._lock = threading.RLock()

    # ---------------------- Vong doi ket noi tho ---------------------------

    def add_connection(self, client_socket: socket.socket) -> None:
        with self._lock:
            self._all_sockets.add(client_socket)

    def remove_connection(self, client_socket: socket.socket) -> None:
        with self._lock:
            self._all_sockets.discard(client_socket)
            stale_usernames = [
                username for username, sock in self._sockets_by_username.items()
                if sock is client_socket
            ]
            for username in stale_usernames:
                self._sockets_by_username.pop(username, None)

    def get_all_connections(self) -> list[socket.socket]:
        with self._lock:
            return list(self._all_sockets)

    def connection_count(self) -> int:
        with self._lock:
            return len(self._all_sockets)

    # ---------------------- Anh xa username <-> socket ---------------------

    def register_username(self, username: str, client_socket: socket.socket) -> bool:
        """Gan username cho socket. Tra ve False neu username da online."""
        with self._lock:
            if username in self._sockets_by_username:
                return False
            self._sockets_by_username[username] = client_socket
            return True

    def unregister_username(self, username: str, client_socket: socket.socket) -> None:
        with self._lock:
            if self._sockets_by_username.get(username) is client_socket:
                self._sockets_by_username.pop(username, None)

    def get_client(self, username: str) -> "socket.socket | None":
        with self._lock:
            return self._sockets_by_username.get(username)

    def get_all_clients(self) -> list[socket.socket]:
        """Socket cua tat ca user da LOGIN (dung cho broadcast)."""
        with self._lock:
            return list(self._sockets_by_username.values())

    def get_online_users(self) -> list[str]:
        with self._lock:
            return list(self._sockets_by_username.keys())