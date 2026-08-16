import socket
import threading
import time

class ClientNetwork:
    def __init__(self, host="127.0.0.1", port=5000, update_gui_callback=None):
        self.host = host
        self.port = port
        self.buffer_size = 4096
        self.encoding = "utf-8"
        
        
        self.update_gui_callback = update_gui_callback 
        
        self.client_socket = None
        self.is_connected = False

    def trigger_ui(self, msg_type, message):
        """Hàm trung gian: Có GUI thì đẩy lên GUI, không có thì in ra Console"""
        if self.update_gui_callback:
            self.update_gui_callback(msg_type, message)
        else:
            print(f"[{msg_type}] {message}")

    def connect(self):
        while not self.is_connected:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.host, self.port))
                self.is_connected = True
                
                self.trigger_ui("SYSTEM", "Da ket noi toi Server!")
                
                # Bắt đầu luồng nhận dữ liệu
                threading.Thread(target=self.receive_messages, daemon=True).start()
                
            except socket.error:
                self.trigger_ui("SYSTEM", "Loi ket noi. Thu lai sau 3s...")
                time.sleep(3)

    def receive_messages(self):
        while self.is_connected:
            try:
                message = self.client_socket.recv(self.buffer_size).decode(self.encoding)
                if message:
                    self.trigger_ui("RECEIVE", message)
                else:
                    self._handle_disconnect()
                    break
            except Exception:
                self._handle_disconnect()
                break

    def send_message(self, message):
        if self.is_connected:
            try:
                self.client_socket.send(message.encode(self.encoding))
            except socket.error:
                self._handle_disconnect()
        else:
            self.trigger_ui("SYSTEM", "Chua ket noi, khong the gui!")

    def _handle_disconnect(self):
        if self.is_connected:
            self.is_connected = False
            self.client_socket.close()
            self.trigger_ui("SYSTEM", "Mat ket noi. Dang ket noi lai...")
            # Tự động kết nối lại
            threading.Thread(target=self.connect, daemon=True).start()

    def disconnect(self):
        self.is_connected = False
        if self.client_socket:
            self.client_socket.close()

if __name__ == "__main__":
    import threading
    
    # Khởi tạo class mạng của bạn
    my_network = ClientNetwork(host="127.0.0.1", port=5000)
    
    # Chạy luồng kết nối ngầm
    threading.Thread(target=my_network.connect, daemon=True).start()
    
    # Vòng lặp liên tục chờ bạn gõ tin nhắn từ bàn phím
    try:
        while True:
            text_to_send = input()
            if text_to_send.lower() == 'quit' or text_to_send.lower() == 'thoat':
                my_network.disconnect()
                break
            if text_to_send:
                my_network.send_message(text_to_send)
    except KeyboardInterrupt:
        my_network.disconnect()