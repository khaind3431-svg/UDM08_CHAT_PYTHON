import threading
import socket


class ClientManager:

    def __init__(self):
        # username -> socket
        self.clients: dict[str, socket.socket] = {}
        self.lock = threading.Lock()

    def add_client(self, username: str, client_socket: socket.socket) -> None:
        with self.lock:
            self.clients[username] = client_socket

    def remove_client(self, username: str) -> None:
        with self.lock:
            if username in self.clients:
                del self.clients[username]

    def get_client(self, username: str):
        with self.lock:
            return self.clients.get(username)

    def get_all_clients(self):
        with self.lock:
            return list(self.clients.values())

    def get_online_users(self):
        with self.lock:
            return list(self.clients.keys())

    def count(self) -> int:
        with self.lock:
            return len(self.clients)

    def is_online(self, username: str) -> bool:
        with self.lock:
            return username in self.clients

    def clear(self) -> None:
        with self.lock:
            self.clients.clear()