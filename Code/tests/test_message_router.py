import unittest

from server.message_router import MessageRouter


class TestMessageRouter(unittest.TestCase):

    def setUp(self):
        self.router = MessageRouter()

    def test_ping(self):
        msg = self.router.route("PING")
        self.assertEqual(msg.message_type, "PING")

    def test_message(self):
        msg = self.router.route("MESSAGE|Hello")
        self.assertEqual(msg.message_type, "MESSAGE")
        self.assertEqual(msg.content, "Hello")

    def test_private(self):
        msg = self.router.route("PRIVATE|Tuan|Xin chao")
        self.assertEqual(msg.message_type, "PRIVATE")
        self.assertEqual(msg.content, "Tuan|Xin chao")

    def test_logout(self):
        msg = self.router.route("LOGOUT")
        self.assertEqual(msg.message_type, "LOGOUT")

    def test_invalid(self):
        with self.assertRaises(ValueError):
            self.router.route("ABC|123")


if __name__ == "__main__":
    unittest.main()