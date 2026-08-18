from Code.backend.utils.server_logger import log
from Code.config.server_config import ENCODING


class OnlineManager:

    def __init__(self, client_manager):
        self.client_manager = client_manager

    def send_online_list(self):
        """
        Gửi danh sách người dùng đang online cho tất cả client.
        """

        users = self.client_manager.get_online_users()

        packet = "ONLINE|" + ",".join(users) + "\n"

        for client_socket in self.client_manager.get_all_clients():

            try:
                client_socket.sendall(packet.encode(ENCODING))

            except OSError:
                pass

        log(f"Cap nhat danh sach online: {users}")