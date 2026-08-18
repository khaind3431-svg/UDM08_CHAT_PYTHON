import socket
import sys
import threading
from pathlib import Path
from typing import Optional

# Ho tro ca hai cach chay:
#   python Code/backend/server_main.py
#   python -m Code.backend.server_main
if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from Code.backend.message_protocol import MessageRouter
from Code.backend.utils.server_logger import log
from Code.config.server_config import (
    ACCEPT_TIMEOUT, BACKLOG, BUFFER_SIZE, CLIENT_TIMEOUT,
    ENCODING, HOST, MAX_CLIENTS, PORT,
)


class ChatServer:
    """
    Server Core cho UDM08 Chat TCP.

    Phan Server nay tu quan ly username <-> socket de khong can sua
    client/client_handler.py hay client/client_manager.py cua thanh vien khac.

    Protocol dang khop voi GUI Client hien tai:
        LOGIN|username
        MESSAGE|content
        PRIVATE|receiver|content
        PING
        LOGOUT

    Server gui:
        SYSTEM|content
        ONLINE|user1,user2
        MESSAGE|sender|content
        PRIVATE|sender|content
        PONG
        ERROR|content
    """

    def __init__(self, host: str = HOST, port: int = PORT) -> None:
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.running = threading.Event()

        # Tat ca socket dang ket noi (ke ca chua LOGIN)
        self.client_sockets: set[socket.socket] = set()
        self.client_threads: set[threading.Thread] = set()

        # username -> socket
        self.online_clients: dict[str, socket.socket] = {}

        self.clients_lock = threading.RLock()
        self.threads_lock = threading.Lock()
        self.router = MessageRouter()

    def start(self) -> None:
        if self.running.is_set():
            raise RuntimeError("Server dang chay.")

        self._create_server_socket()
        self.running.set()

        log(f"Server dang chay tai {self.host}:{self.port}")
        log("Dang cho Client ket noi...")

        try:
            self._accept_loop()
        except KeyboardInterrupt:
            log("Nhan Ctrl+C. Dang dung Server...")
        finally:
            self.stop()

    def _create_server_socket(self) -> None:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(BACKLOG)
        server_socket.settimeout(ACCEPT_TIMEOUT)
        self.server_socket = server_socket

    def _accept_loop(self) -> None:
        if self.server_socket is None:
            raise RuntimeError("Server socket chua khoi tao.")

        while self.running.is_set():
            try:
                client_socket, client_address = self.server_socket.accept()
            except socket.timeout:
                self._remove_finished_threads()
                continue
            except OSError:
                if self.running.is_set():
                    raise
                break

            if self.get_client_count() >= MAX_CLIENTS:
                self._reject_client(client_socket)
                continue

            client_socket.settimeout(CLIENT_TIMEOUT)

            with self.clients_lock:
                self.client_sockets.add(client_socket)

            log(
                f"Client ket noi: {client_address[0]}:{client_address[1]} "
                f"| Tong ket noi: {self.get_client_count()}"
            )

            client_thread = threading.Thread(
                target=self._client_worker,
                args=(client_socket, client_address),
                daemon=True,
            )
            with self.threads_lock:
                self.client_threads.add(client_thread)
            client_thread.start()

    def _client_worker(self, client_socket: socket.socket, client_address) -> None:
        username: Optional[str] = None
        buffer = ""

        try:
            self._send_text(client_socket, "SYSTEM|Ket noi Server thanh cong.")

            while self.running.is_set():
                try:
                    data = client_socket.recv(BUFFER_SIZE)
                except socket.timeout:
                    continue

                if not data:
                    break

                buffer += data.decode(ENCODING)

                # Client gui ket thuc moi packet bang \n.
                # Xu ly theo dong de tranh 2 packet bi dinh vao nhau.
                while "\n" in buffer:
                    raw_message, buffer = buffer.split("\n", 1)
                    raw_message = raw_message.strip()
                    if not raw_message:
                        continue

                    try:
                        routed = self.router.route(raw_message)
                    except ValueError as error:
                        self._send_text(client_socket, f"ERROR|{error}")
                        continue

                    msg_type = routed.message_type

                    # LOGIN -------------------------------------------------
                    if msg_type == "LOGIN":
                        if username is not None:
                            self._send_text(client_socket, "ERROR|Ban da dang nhap.")
                            continue

                        candidate = routed.content.strip()

                        if not self._valid_username(candidate):
                            self._send_text(
                                client_socket,
                                "ERROR|Username khong hop le."
                            )
                            continue

                        if not self._register_username(candidate, client_socket):
                            self._send_text(
                                client_socket,
                                "ERROR|Ten dang nhap da ton tai."
                            )
                            continue

                        username = candidate
                        log(
                            f"{username} dang nhap tu "
                            f"{client_address[0]}:{client_address[1]}"
                        )
                        self._send_text(
                            client_socket,
                            f"SYSTEM|Xin chao {username}!"
                        )
                        self._send_online_list()
                        self._broadcast(
                            "SYSTEM",
                            f"{username} da tham gia phong chat."
                        )

                    # Bat buoc LOGIN truoc cac chuc nang nguoi dung ----------
                    elif msg_type in {"MESSAGE", "PRIVATE"} and username is None:
                        self._send_text(
                            client_socket,
                            "ERROR|Ban phai LOGIN truoc."
                        )

                    # MESSAGE -----------------------------------------------
                    elif msg_type == "MESSAGE":
                        log(f"[MESSAGE] {username}: {routed.content}")
                        self._broadcast(username, routed.content)

                    # PRIVATE -----------------------------------------------
                    elif msg_type == "PRIVATE":
                        receiver, content = self._parse_private(routed.content)
                        if receiver is None:
                            self._send_text(
                                client_socket,
                                "ERROR|PRIVATE dung dang: PRIVATE|NguoiNhan|NoiDung"
                            )
                            continue

                        if self._send_private(username, receiver, content):
                            # Echo lai sender de biet gui thanh cong.
                            if receiver != username:
                                self._send_text(
                                    client_socket,
                                    f"PRIVATE|{username}|To {receiver}: {content}"
                                )
                        else:
                            self._send_text(
                                client_socket,
                                f"ERROR|Nguoi dung {receiver} khong online."
                            )

                    # PING --------------------------------------------------
                    elif msg_type == "PING":
                        self._send_text(client_socket, "PONG")

                    # LOGOUT ------------------------------------------------
                    elif msg_type == "LOGOUT":
                        break

        except UnicodeDecodeError:
            self._send_text_safely(
                client_socket,
                "ERROR|Du lieu phai dung UTF-8."
            )
            log("Client gui du lieu khong dung UTF-8.")
        except (ConnectionResetError, ConnectionAbortedError):
            log("Client mat ket noi.")
        except OSError as error:
            if self.running.is_set():
                log(f"Loi Client: {error}")
        finally:
            if username is not None:
                self._unregister_username(username, client_socket)
                self._broadcast(
                    "SYSTEM",
                    f"{username} da roi phong chat."
                )
                self._send_online_list()

            self._remove_client_socket(client_socket)
            self._remove_current_thread()

            log(
                f"Client roi Server: {client_address[0]}:{client_address[1]} "
                f"| Con lai: {self.get_client_count()}"
            )

    # ---------------------- QUAN LY USER ---------------------------------

    @staticmethod
    def _valid_username(username: str) -> bool:
        if not username or len(username) > 30:
            return False
        # Ky tu | va newline lam hong protocol dang text.
        return "|" not in username and "\n" not in username and "\r" not in username

    def _register_username(
        self, username: str, client_socket: socket.socket
    ) -> bool:
        with self.clients_lock:
            if username in self.online_clients:
                return False
            self.online_clients[username] = client_socket
            return True

    def _unregister_username(
        self, username: str, client_socket: socket.socket
    ) -> None:
        with self.clients_lock:
            if self.online_clients.get(username) is client_socket:
                self.online_clients.pop(username, None)

    def get_online_users(self) -> list[str]:
        with self.clients_lock:
            return list(self.online_clients.keys())

    # ---------------------- CHAT -----------------------------------------

    def _broadcast(self, sender: str, message: str) -> None:
        packet = f"MESSAGE|{sender}|{message}"
        disconnected: list[socket.socket] = []

        with self.clients_lock:
            targets = list(self.online_clients.values())

        for sock in targets:
            try:
                self._send_text(sock, packet)
            except OSError:
                disconnected.append(sock)

        for sock in disconnected:
            self._remove_client_socket(sock)

    def _send_online_list(self) -> None:
        users = self.get_online_users()
        packet = "ONLINE|" + ",".join(users)

        with self.clients_lock:
            targets = list(self.online_clients.values())

        for sock in targets:
            self._send_text_safely(sock, packet)

        log(f"Online: {users}")

    @staticmethod
    def _parse_private(content: str):
        # Router da cat "PRIVATE|" dau tien.
        # Con lai phai la receiver|message
        parts = content.split("|", 1)
        if len(parts) != 2:
            return None, None

        receiver = parts[0].strip()
        message = parts[1].strip()

        if not receiver or not message:
            return None, None
        return receiver, message

    def _send_private(
        self, sender: str, receiver: str, message: str
    ) -> bool:
        with self.clients_lock:
            receiver_socket = self.online_clients.get(receiver)

        if receiver_socket is None:
            return False

        try:
            self._send_text(
                receiver_socket,
                f"PRIVATE|{sender}|{message}"
            )
            log(f"[PRIVATE] {sender} -> {receiver}: {message}")
            return True
        except OSError:
            return False

    # ---------------------- SOCKET / THREAD -------------------------------

    def _reject_client(self, client_socket: socket.socket) -> None:
        try:
            self._send_text(
                client_socket,
                "ERROR|Server da dat gioi han Client."
            )
        except OSError:
            pass
        finally:
            try:
                client_socket.close()
            except OSError:
                pass

    @staticmethod
    def _send_text(client_socket: socket.socket, message: str) -> None:
        client_socket.sendall((message + "\n").encode(ENCODING))

    def _send_text_safely(
        self, client_socket: socket.socket, message: str
    ) -> None:
        try:
            self._send_text(client_socket, message)
        except OSError:
            pass

    def _remove_client_socket(self, client_socket: socket.socket) -> None:
        with self.clients_lock:
            self.client_sockets.discard(client_socket)

            stale_users = [
                name for name, sock in self.online_clients.items()
                if sock is client_socket
            ]
            for name in stale_users:
                self.online_clients.pop(name, None)

        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            client_socket.close()
        except OSError:
            pass

    def _remove_current_thread(self) -> None:
        current = threading.current_thread()
        with self.threads_lock:
            self.client_threads.discard(current)

    def _remove_finished_threads(self) -> None:
        with self.threads_lock:
            self.client_threads = {
                thread for thread in self.client_threads if thread.is_alive()
            }

    def get_client_count(self) -> int:
        with self.clients_lock:
            return len(self.client_sockets)

    def stop(self) -> None:
        if not self.running.is_set() and self.server_socket is None:
            return

        self.running.clear()

        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except OSError:
                pass
            self.server_socket = None

        with self.clients_lock:
            sockets = list(self.client_sockets)

        for client_socket in sockets:
            self._remove_client_socket(client_socket)

        with self.clients_lock:
            self.online_clients.clear()

        log("Server da dung.")


if __name__ == "__main__":
    ChatServer().start()
