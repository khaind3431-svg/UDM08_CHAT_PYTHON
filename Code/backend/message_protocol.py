from dataclasses import dataclass


@dataclass(frozen=True)
class RoutedMessage:
    message_type: str
    content: str


class MessageRouter:
    # Khop voi protocol text ma Client GUI hien tai dang gui.
    SUPPORTED_TYPES = {
        "LOGIN",
        "REGISTER",
        "PING",
        "MESSAGE",
        "PRIVATE",
        "REPLY",
        "FORWARD",
        "LOGOUT",
        # --- Ket ban ---
        "ADDFRIEND",
        "FRIEND_RESP",
        "FRIENDLIST",
        "FRIENDREQUESTS",
        "GETINFO"
    }

    # FRIENDLIST va FRIENDREQUESTS khong can noi dung (chi username dang
    # dang nhap la du de server tra loi), nen khong nam trong danh sach
    # bat buoc co content ben duoi.
    _REQUIRES_CONTENT = {
        "LOGIN", "REGISTER", "MESSAGE", "PRIVATE", "REPLY", "FORWARD",
        "ADDFRIEND", "FRIEND_RESP", "GETINFO",
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

        if message_type in self._REQUIRES_CONTENT and not content:
            raise ValueError(
                f"{message_type} yeu cau noi dung."
            )

        return RoutedMessage(message_type, content)