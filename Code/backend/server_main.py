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


from Code.backend.controllers.auth_controller import AuthController
from Code.backend.controllers.chat_controller import ChatController
from Code.backend.controllers.contact_controller import ContactController
from Code.backend.controllers.profile_controller import ProfileController
from Code.backend.core.client_handler import ClientHandler
from Code.backend.core.client_manager import ClientManager
from Code.backend.core.session_manager import OnlineManager
from Code.backend.message_protocol import MessageRouter
from Code.backend.services.broadcast_service import Broadcaster
from Code.backend.services.private_chat_service import PrivateChat
from Code.backend.utils.server_logger import log
from Code.config.server_config import (
    ACCEPT_TIMEOUT,
    BACKLOG,
    BUFFER_SIZE,
    CLIENT_TIMEOUT,
    ENCODING,
    HOST,
    MAX_CLIENTS,
    PORT,
)


class ChatServer:

    def __init__(self, host: str = HOST, port: int = PORT) -> None:
        self.host = host
        self.port = port

        self.server_socket: Optional[socket.socket] = None
        self.running = threading.Event()

        self.client_threads: set[threading.Thread] = set()
        self.threads_lock = threading.Lock()

        # =====================================================
        # LAP RAP CAC THANH PHAN
        # =====================================================

        self.client_manager = ClientManager()
        self.router = MessageRouter()

        self.online_manager = OnlineManager(
            self.client_manager
        )

        self.broadcaster = Broadcaster(
            self.client_manager
        )

        self.private_chat = PrivateChat(
            self.client_manager
        )

        self.auth_controller = AuthController(
            self.client_manager,
            self.online_manager,
            self.broadcaster,
        )

        self.chat_controller = ChatController(
            self.client_manager,
            self.broadcaster,
            self.private_chat,
            get_user_id=lambda username:
                self.auth_controller.user_ids.get(username),
        )

        self.contact_controller = ContactController(
            self.client_manager
        )
        self.profile_controller = ProfileController(
            get_user_id=lambda username:
                self.auth_controller.user_ids.get(username),
        )

    # =========================================================
    # START SERVER
    # =========================================================

    def start(self) -> None:

        if self.running.is_set():
            raise RuntimeError("Server dang chay.")

        self._create_server_socket()
        self.running.set()

        log(
            f"Server dang chay tai "
            f"{self.host}:{self.port}"
        )

        log("Dang cho Client ket noi...")

        try:
            self._accept_loop()

        except KeyboardInterrupt:
            log("Nhan Ctrl+C. Dang dung Server...")

        finally:
            self.stop()

    # =========================================================
    # CREATE SERVER SOCKET
    # =========================================================

    def _create_server_socket(self) -> None:

        server_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        )

        server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        server_socket.bind(
            (
                self.host,
                self.port,
            )
        )

        server_socket.listen(BACKLOG)
        server_socket.settimeout(ACCEPT_TIMEOUT)

        self.server_socket = server_socket

    # =========================================================
    # ACCEPT CLIENT LOOP
    # =========================================================

    def _accept_loop(self) -> None:

        if self.server_socket is None:
            raise RuntimeError(
                "Server socket chua khoi tao."
            )

        while self.running.is_set():

            try:
                client_socket, client_address = (
                    self.server_socket.accept()
                )

            except socket.timeout:
                self._remove_finished_threads()
                continue

            except OSError:
                if self.running.is_set():
                    raise

                break

            if (
                self.client_manager.connection_count()
                >= MAX_CLIENTS
            ):
                self._reject_client(client_socket)
                continue

            client_socket.settimeout(CLIENT_TIMEOUT)

            self.client_manager.add_connection(
                client_socket
            )

            log(
                f"Client ket noi: "
                f"{client_address[0]}:"
                f"{client_address[1]} "
                f"| Tong ket noi: "
                f"{self.client_manager.connection_count()}"
            )

            handler = ClientHandler(
                client_socket,
                client_address,
                router=self.router,
                auth_controller=self.auth_controller,
                chat_controller=self.chat_controller,
                contact_controller=self.contact_controller,
                profile_controller=self.profile_controller,
                running_flag=self.running,
            )

            client_thread = threading.Thread(
                target=self._run_handler,
                args=(
                    handler,
                    client_address,
                ),
                daemon=True,
            )

            with self.threads_lock:
                self.client_threads.add(
                    client_thread
                )

            client_thread.start()

    # =========================================================
    # RUN CLIENT HANDLER
    # =========================================================

    def _run_handler(
        self,
        handler: ClientHandler,
        client_address,
    ) -> None:

        try:
            handler.run()

        finally:
            self.auth_controller.handle_disconnect(
                handler.username,
                handler.socket,
            )

            self.client_manager.remove_connection(
                handler.socket
            )

            self._close_socket(
                handler.socket
            )

            self._remove_current_thread()

            log(
                f"Client roi Server: "
                f"{client_address[0]}:"
                f"{client_address[1]} "
                f"| Con lai: "
                f"{self.client_manager.connection_count()}"
            )

    # =========================================================
    # REJECT CLIENT
    # =========================================================

    def _reject_client(
        self,
        client_socket: socket.socket,
    ) -> None:

        try:
            client_socket.sendall(
                (
                    "ERROR|Server da dat "
                    "gioi han Client.\n"
                ).encode(ENCODING)
            )

        except OSError:
            pass

        finally:
            self._close_socket(
                client_socket
            )

    # =========================================================
    # CLOSE SOCKET
    # =========================================================

    @staticmethod
    def _close_socket(
        client_socket: socket.socket,
    ) -> None:

        try:
            client_socket.shutdown(
                socket.SHUT_RDWR
            )

        except OSError:
            pass

        try:
            client_socket.close()

        except OSError:
            pass

    # =========================================================
    # REMOVE CURRENT THREAD
    # =========================================================

    def _remove_current_thread(self) -> None:

        current = threading.current_thread()

        with self.threads_lock:
            self.client_threads.discard(
                current
            )

    # =========================================================
    # REMOVE FINISHED THREADS
    # =========================================================

    def _remove_finished_threads(self) -> None:

        with self.threads_lock:
            self.client_threads = {
                thread
                for thread in self.client_threads
                if thread.is_alive()
            }

    # =========================================================
    # STOP SERVER
    # =========================================================

    def stop(self) -> None:

        if (
            not self.running.is_set()
            and self.server_socket is None
        ):
            return

        self.running.clear()

        if self.server_socket is not None:

            try:
                self.server_socket.close()

            except OSError:
                pass

            self.server_socket = None

        for client_socket in (
            self.client_manager.get_all_connections()
        ):
            self._close_socket(
                client_socket
            )

        log("Server da dung.")


if __name__ == "__main__":
    ChatServer().start()
