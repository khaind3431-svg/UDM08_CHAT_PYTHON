# UDM08_CHAT_PYTHON

> Ứng dụng Chat Client--Server sử dụng TCP Socket bằng Python (GUI)

## 1. Giới thiệu

Đây là đồ án môn **Lập trình mạng** xây dựng ứng dụng chat theo mô hình
**Client -- Server**. Ứng dụng sử dụng **TCP Socket**, giao diện
**Tkinter**, giao thức **JSON** và **SQLite** để lưu lịch sử trò chuyện.

### Chức năng chính

-   Đăng nhập
-   Chat thời gian thực
-   Chat riêng
-   Danh sách người dùng Online
-   Reply tin nhắn
-   Forward tin nhắn
-   Emoji
-   Lưu lịch sử trò chuyện bằng SQLite

------------------------------------------------------------------------

# 2. Công nghệ sử dụng

  Thành phần    Công nghệ
  ------------- ------------
  Ngôn ngữ      Python 3
  Giao diện     Tkinter
  Network       TCP Socket
  Database      SQLite
  Data Format   JSON
  Đa luồng      threading

------------------------------------------------------------------------

# 3. Kiến trúc hệ thống

``` text
Client GUI
     │
 TCP Socket
     │
Server
     │
Message Router
     │
Database (SQLite)
```

------------------------------------------------------------------------

# 4. Cấu trúc Project

``` text
client/
database/
server/
shared/
tests/
tools/
```

------------------------------------------------------------------------

# 5. Mô tả các thư mục

## client

-   chat_window.py
-   client_handler.py
-   client_manager.py
-   client_network.py

Quản lý giao diện và kết nối từ phía Client.

## server

-   server.py
-   broadcaster.py
-   message_router.py
-   online_manager.py
-   private_chat.py
-   server_logger.py

Quản lý toàn bộ Server.

## database

db_manager.py

Lưu lịch sử chat SQLite.

## shared

protocol.py

Định nghĩa giao thức JSON.

## tests

Các bài kiểm thử.

------------------------------------------------------------------------

# 6. Giao thức

Ví dụ:

``` json
{
 "action":"CHAT",
 "sender":"userA",
 "receiver":"userB",
 "content":"Hello"
}
```

------------------------------------------------------------------------

# 7. Hướng dẫn chạy

## Cài đặt

``` bash
pip install pillow
```

## Chạy Server

``` bash
python server/server.py
```

## Chạy Client

``` bash
python client/chat_window.py
```

------------------------------------------------------------------------

# 8. Kiểm thử

``` bash
python test_my_module.py
```

Hoặc

``` bash
pytest tests
```

------------------------------------------------------------------------

# 9. Chức năng đã hoàn thành

-   GUI
-   TCP Socket
-   JSON Protocol
-   SQLite
-   Private Chat
-   Online List
-   Logging
-   Reply
-   Forward
-   Emoji

------------------------------------------------------------------------

# 10. Hạn chế

-   Chưa mã hóa dữ liệu.
-   Chưa gửi file.
-   Chưa hỗ trợ Voice/Video.

------------------------------------------------------------------------

# 11. Hướng phát triển

-   Gửi file
-   Mã hóa AES
-   Video Call
-   Cloud Database
-   Mobile Client

------------------------------------------------------------------------

# 12. Thành viên

  MSSV   Họ tên            Công việc
  ------ ----------------- ------------------------
  ...    Trần Thanh Hải          Client Handler
  ...    Phan Triều Cường        GUI
  ...    Nguyễn Võ Tấn Phát      Client Network
  ...    Phan Tấn Tài            Protocol + Database
  ...    Nguyễn Hồ Minh Hiển     Private Chat + Testing
  ...    Nguyễn Đức Khải         Server Core

------------------------------------------------------------------------


# 13. License

MIT License.
