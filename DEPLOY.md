# Hướng dẫn triển khai hệ thống Chat TCP

## Mục đích

Tài liệu này hướng dẫn cấu hình và triển khai hệ thống Chat TCP để Client có thể kết nối tới Server thông qua mạng LAN.

---

## 1. Cấu hình Server

Trong file `server/config.py`:

```python
HOST = "0.0.0.0"
PORT = 5000
```

Trong đó:

- `0.0.0.0`: Cho phép Server lắng nghe trên tất cả địa chỉ mạng.
- `5000`: Cổng TCP dùng để giao tiếp giữa Server và Client.

---

## 2. Lấy địa chỉ IP của Server

Trên máy chạy Server mở Command Prompt và nhập:

```bash
ipconfig
```

Tìm dòng:

```
IPv4 Address
```

Ví dụ:

```
192.168.20.106
```

Đây là địa chỉ IP để Client kết nối.

---

## 3. Cấu hình Client

Nếu chạy trên cùng máy:

```python
HOST = "127.0.0.1"
PORT = 5000
```

Nếu chạy trên máy khác cùng mạng LAN:

```python
HOST = "192.168.20.106"
PORT = 5000
```

Trong đó `192.168.20.106` là địa chỉ IP của máy chạy Server.

---

## 4. Khởi động chương trình

### Chạy Server

```bash
python server/server.py
```

### Chạy Client

```bash
python client/chat_window.py
```

---

## 5. Kiểm tra kết nối

Khi Client kết nối thành công, Server sẽ hiển thị thông tin Client vừa kết nối.

Nếu kiểm tra trên cùng máy sẽ hiển thị địa chỉ:

```
127.0.0.1
```

Nếu triển khai trên hai máy cùng mạng LAN sẽ hiển thị địa chỉ IP nội bộ của Client.

---

## 6. Lưu ý

- Hai máy phải kết nối cùng mạng LAN hoặc Wi-Fi.
- Server phải được khởi động trước Client.
- Client cần nhập đúng địa chỉ IP của máy Server.
- Nếu bị chặn kết nối, cần mở cổng TCP 5000 trong Windows Defender Firewall.