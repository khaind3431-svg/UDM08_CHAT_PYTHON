from dataclasses import dataclass

@dataclass(frozen=True)
class RoutedMessage:
    message_type: str
    content: str

class MessageRouter:
    SUPPORTED_TYPES = {"PING", "MESSAGE", "LOGOUT"}

    def route(self, raw_message: str) -> RoutedMessage:
        raw_message = raw_message.strip()
        if not raw_message:
            raise ValueError("Thong diep rong.")

        parts = raw_message.split("|", 1)
        message_type = parts[0].upper()
        content = parts[1].strip() if len(parts) == 2 else ""

        if message_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"Loai thong diep khong ho tro: {message_type}")

        if message_type == "MESSAGE" and not content:
            raise ValueError("Noi dung tin nhan khong duoc de trong.")

        return RoutedMessage(message_type, content)
