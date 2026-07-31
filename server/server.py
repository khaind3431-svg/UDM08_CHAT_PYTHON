import socket
import threading
from typing import Optional

from config import (
    ACCEPT_TIMEOUT,
    BACKLOG,
    BUFFER_SIZE,
    CLIENT_TIMEOUT,
    ENCODING,
    HOST,
    MAX_CLIENTS,
    PORT,
)
from message_router import MessageRouter
from server_logger import log

class ChatServer:
    def __init__(self, host: str = HOST, port: int = PORT) -> None:
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.running = threading.Event()
        self.client_sockets: set[socket.socket] = set()
        self.client_threads: set[threading.Thread] = set()
        self.clients_lock = threading.Lock()
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
                f"| Tong: {self.get_client_count()}"
            )

            client_thread = threading.Thread(
                target=self._client_worker,
                args=(client_socket, client_address),
                daemon=True,
            )

            with self.threads_lock:
                self.client_threads.add(client_thread)

            client_thread.start()

    def _client_worker(self, client_socket, client_address) -> None:
        try:
            self._send_text(client_socket, "SYSTEM|Ket noi Server thanh cong.")

            while self.running.is_set():
                try:
                    data = client_socket.recv(BUFFER_SIZE)
                except socket.timeout:
                    continue

                if not data:
                    break

                raw_message = data.decode(ENCODING).strip()

                try:
                    routed = self.router.route(raw_message)
                except ValueError as error:
                    self._send_text(client_socket, f"ERROR|{error}")
                    continue

                if routed.message_type == "PING":
                    self._send_text(client_socket, "PONG")

                elif routed.message_type == "MESSAGE":
                    log(
                        f"Nhan tu {client_address[0]}:{client_address[1]} "
                        f"-> {routed.content}"
                    )
                    self._send_text(
                        client_socket,
                        f"ACK|Server da nhan: {routed.content}",
                    )

                elif routed.message_type == "LOGOUT":
                    break

        except UnicodeDecodeError:
            log("Client gui du lieu khong dung UTF-8.")
        except (ConnectionResetError, ConnectionAbortedError):
            log("Client mat ket noi.")
        except OSError as error:
            if self.running.is_set():
                log(f"Loi Client: {error}")
        finally:
            self._remove_client(client_socket)
            self._remove_current_thread()
            log(
                f"Client roi Server: {client_address[0]}:{client_address[1]} "
                f"| Con lai: {self.get_client_count()}"
            )

    def _reject_client(self, client_socket: socket.socket) -> None:
        try:
            self._send_text(client_socket, "ERROR|Server da dat gioi han Client.")
        except OSError:
            pass
        finally:
            client_socket.close()

    @staticmethod
    def _send_text(client_socket: socket.socket, message: str) -> None:
        client_socket.sendall((message + "\n").encode(ENCODING))

    def get_client_count(self) -> int:
        with self.clients_lock:
            return len(self.client_sockets)

    def _remove_client(self, client_socket: socket.socket) -> None:
        with self.clients_lock:
            self.client_sockets.discard(client_socket)

        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            client_socket.close()
        except OSError:
            pass

    def _remove_current_thread(self) -> None:
        current_thread = threading.current_thread()
        with self.threads_lock:
            self.client_threads.discard(current_thread)

    def _remove_finished_threads(self) -> None:
        with self.threads_lock:
            self.client_threads = {
                thread for thread in self.client_threads if thread.is_alive()
            }

    def stop(self) -> None:
        if not self.running.is_set() and self.server_socket is None:
            return

        self.running.clear()
        log("Dang dong cac ket noi...")

        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except OSError:
                pass
            self.server_socket = None

        with self.clients_lock:
            sockets = list(self.client_sockets)

        for client_socket in sockets:
            self._remove_client(client_socket)

        log("Server da dung.")

if __name__ == "__main__":
    ChatServer().start()
