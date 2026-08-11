# broadcaster.py

import socket

from config import ENCODING
from server_logger import log


class Broadcaster:

    def __init__(self, client_manager):
        self.client_manager = client_manager

    def broadcast(self, sender: str, message: str) -> None:
        """
        Gửi tin nhắn đến tất cả client đang online.
        """

        packet = f"MESSAGE|{sender}|{message}\n"

        disconnected = []

        for client_socket in self.client_manager.get_all_clients():

            try:
                client_socket.sendall(packet.encode(ENCODING))

            except (ConnectionResetError,
                    ConnectionAbortedError,
                    BrokenPipeError,
                    OSError):

                disconnected.append(client_socket)

        # Có thể log nếu cần
        log(f"Broadcast từ [{sender}]: {message}")