"""
ClientHandler - vong doi xu ly cho mot ket noi client.

Doc du lieu tho tu socket, tach goi theo dong (\n), dua qua
MessageRouter de phan loai loai thong diep, roi giao cho dung
Controller (AuthController / ChatController) xu ly nghiep vu.
"""

import socket
import threading
from typing import Optional

from Code.backend.message_protocol import MessageRouter
from Code.config.server_config import BUFFER_SIZE, ENCODING

# Cac loai thong diep bat buoc phai LOGIN truoc moi duoc dung.
_REQUIRES_LOGIN = {"MESSAGE", "PRIVATE", "REPLY", "FORWARD", "IMAGE"}


class ClientHandler:
    def __init__(
        self,
        client_socket: socket.socket,
        client_address,
        *,
        router: MessageRouter,
        auth_controller,
        chat_controller,
        running_flag: threading.Event,
    ) -> None:
        self.socket = client_socket
        self.address = client_address
        self.router = router
        self.auth_controller = auth_controller
        self.chat_controller = chat_controller
        self.running = running_flag
        self.username: Optional[str] = None

    def run(self) -> None:
        """Vong lap chinh cho 1 ket noi. Tra ve khi client LOGOUT,
        ngat ket noi, hoac server dang dung."""
        buffer = ""
        try:
            self._send(self.socket, "SYSTEM|Ket noi Server thanh cong.")

            while self.running.is_set():
                try:
                    data = self.socket.recv(BUFFER_SIZE)
                except socket.timeout:
                    continue

                if not data:
                    break

                buffer += data.decode(ENCODING)

                # Client ket thuc moi packet bang \n; xu ly tung dong de
                # tranh 2 packet dinh vao nhau trong 1 lan recv().
                while "\n" in buffer:
                    raw_message, buffer = buffer.split("\n", 1)
                    raw_message = raw_message.strip()
                    if not raw_message:
                        continue
                    if not self._handle_line(raw_message):
                        return  # LOGOUT

        except UnicodeDecodeError:
            self._send_safe(self.socket, "ERROR|Du lieu phai dung UTF-8.")
        except (ConnectionResetError, ConnectionAbortedError):
            pass
        except OSError:
            if self.running.is_set():
                raise

    def _handle_line(self, raw_message: str) -> bool:
        """Xu ly 1 dong da tach. Tra ve False de bao hieu ngung vong lap
        (LOGOUT), True de tiep tuc."""
        try:
            routed = self.router.route(raw_message)
        except ValueError as error:
            self._send(self.socket, f"ERROR|{error}")
            return True

        msg_type = routed.message_type

        if msg_type in {"LOGIN", "REGISTER"}:
            result_username = self.auth_controller.handle(
                msg_type, routed.content, self.socket, self.address
            )
            if result_username is not None:
                self.username = result_username
            return True

        if msg_type in _REQUIRES_LOGIN and self.username is None:
            self._send(self.socket, "ERROR|Ban phai LOGIN truoc.")
            return True

        if msg_type in _REQUIRES_LOGIN:
            self.chat_controller.handle(msg_type, routed.content, self.username, self.socket)
            return True

        if msg_type == "PING":
            self._send(self.socket, "PONG")
            return True

        if msg_type == "LOGOUT":
            return False

        return True

    @staticmethod
    def _send(client_socket: socket.socket, message: str) -> None:
        client_socket.sendall((message + "\n").encode(ENCODING))

    @staticmethod
    def _send_safe(client_socket: socket.socket, message: str) -> None:
        try:
            client_socket.sendall((message + "\n").encode(ENCODING))
        except OSError:
            pass
