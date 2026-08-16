import os
import sys
import unittest

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

SERVER_DIR = os.path.join(PROJECT_ROOT, "Code", "server")

if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from private_chat import PrivateChat

class FakeSocket:
    def __init__(self):
        self.sent_data = b""
        self.should_fail = False

    def sendall(self, data):
        if self.should_fail:
            raise OSError("Loi socket gia lap")

        self.sent_data = data


class FakeClientManager:
    def __init__(self):
        self.clients = {}

    def add_client(self, username, client_socket):
        self.clients[username] = client_socket

    def get_client(self, username):
        return self.clients.get(username)


class TestPrivateChat(unittest.TestCase):

    def setUp(self):
        self.manager = FakeClientManager()
        self.tuan_socket = FakeSocket()

        self.manager.add_client("Tuan", self.tuan_socket)
        self.private_chat = PrivateChat(self.manager)

    def test_send_private_success(self):
        result = self.private_chat.send_private(
            sender="Anh",
            receiver="Tuan",
            message="Xin chao Tuan"
        )

        self.assertTrue(result)
        self.assertEqual(
            self.tuan_socket.sent_data,
            b"PRIVATE|Anh|Xin chao Tuan\n"
        )

    def test_receiver_not_online(self):
        result = self.private_chat.send_private(
            sender="Anh",
            receiver="KhongTonTai",
            message="Hello"
        )

        self.assertFalse(result)

    def test_socket_error(self):
        self.tuan_socket.should_fail = True

        result = self.private_chat.send_private(
            sender="Anh",
            receiver="Tuan",
            message="Hello"
        )

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()