import socket

from config import BUFFER_SIZE, ENCODING
from server_logger import log


class ClientHandler:

    def __init__(
        self,
        client_socket: socket.socket,
        client_address,
        router,
        client_manager,
        broadcaster,
        online_manager,
    ):
        self.client_socket = client_socket
        self.client_address = client_address

        self.router = router
        self.client_manager = client_manager
        self.broadcaster = broadcaster
        self.online_manager = online_manager

        self.username = None
        self.message_count = 0

    def handle(self):

        self.send("SYSTEM|Ket noi thanh cong.")
        self.send("SYSTEM|Hay dang nhap bang: LOGIN|TenCuaBan")

        try:

            while True:

                data = self.client_socket.recv(BUFFER_SIZE)

                if not data:
                    break

                raw_message = data.decode(ENCODING).strip()

                # ---------------- Parse message ----------------

                try:
                    routed = self.router.route(raw_message)

                except ValueError as e:
                    self.send(f"ERROR|{e}")
                    continue

                # ---------------- LOGIN ----------------

                if routed.message_type == "LOGIN":

                    if self.username is not None:
                        self.send("ERROR|Ban da dang nhap.")
                        continue

                    username = routed.content.strip()

                    if self.client_manager.is_online(username):
                        self.send("ERROR|Ten dang nhap da ton tai.")
                        continue

                    self.username = username

                    self.client_manager.add_client(
                        self.username,
                        self.client_socket
                    )

                    log(
                        f"{self.username} "
                        f"({self.client_address[0]}:{self.client_address[1]}) "
                        "da dang nhap."
                    )

                    self.send(
                        f"SYSTEM|Xin chao {self.username}!"
                    )

                    self.send(
                        f"SYSTEM|Dang co {self.client_manager.count()} nguoi online."
                    )

                    self.online_manager.send_online_list()

                    self.broadcaster.broadcast(
                        "SYSTEM",
                        f"{self.username} da tham gia phong chat."
                    )

                # ---------------- MESSAGE ----------------

                elif routed.message_type == "MESSAGE":

                    if self.username is None:
                        self.send("ERROR|Ban phai LOGIN truoc.")
                        continue

                    self.message_count += 1

                    log(f"{self.username}: {routed.content}")

                    self.broadcaster.broadcast(
                        self.username,
                        routed.content
                    )

                # ---------------- PING ----------------

                elif routed.message_type == "PING":

                    self.send("PONG")

                # ---------------- LOGOUT ----------------

                elif routed.message_type == "LOGOUT":

                    log(f"{self.username} logout.")

                    break

        except (
            ConnectionResetError,
            ConnectionAbortedError,
            OSError,
        ):
            pass

        finally:

            if self.username:

                self.client_manager.remove_client(
                    self.username
                )

                self.broadcaster.broadcast(
                    "SYSTEM",
                    f"{self.username} da roi phong chat."
                )

                self.online_manager.send_online_list()

                log(
                    f"{self.username} da gui "
                    f"{self.message_count} tin nhan."
                )

            try:
                self.client_socket.close()

            except OSError:
                pass

            log(
                f"{self.client_address[0]}:{self.client_address[1]} "
                "da ngat ket noi."
            )

    def send(self, message: str):

        try:
            self.client_socket.sendall(
                (message + "\n").encode(ENCODING)
            )

        except OSError:
            pass