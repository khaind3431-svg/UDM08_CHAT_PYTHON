from config import ENCODING
from server_logger import log


class PrivateChat:

    def __init__(self, client_manager):
        self.client_manager = client_manager

    def send_private(self, sender: str, receiver: str, message: str):
        """
        Gửi tin nhắn riêng từ sender đến receiver.
        """

        receiver_socket = self.client_manager.get_client(receiver)

        if receiver_socket is None:
            return False

        packet = f"PRIVATE|{sender}|{message}\n"

        try:
            receiver_socket.sendall(packet.encode(ENCODING))
            log(f"[PRIVATE] {sender} -> {receiver}: {message}")
            return True

        except OSError:
            return False