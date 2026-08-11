from dataclasses import dataclass


@dataclass(frozen=True)
class RoutedMessage:
    message_type: str
    content: str


class MessageRouter:
    # Khop voi protocol text ma Client GUI hien tai dang gui.
    SUPPORTED_TYPES = {
        "LOGIN",
        "PING",
        "MESSAGE",
        "PRIVATE",
        "LOGOUT",
    }

    def route(self, raw_message: str) -> RoutedMessage:
        raw_message = raw_message.strip()

        if not raw_message:
            raise ValueError("Thong diep rong.")

        parts = raw_message.split("|", 1)
        message_type = parts[0].upper()
        content = parts[1].strip() if len(parts) == 2 else ""

        if message_type not in self.SUPPORTED_TYPES:
            raise ValueError(
                f"Loai thong diep khong ho tro: {message_type}"
            )

        if message_type in {"LOGIN", "MESSAGE", "PRIVATE"} and not content:
            raise ValueError(
                f"{message_type} yeu cau noi dung."
            )

        return RoutedMessage(message_type, content)
