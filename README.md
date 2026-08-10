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

## 📁 Cấu trúc dự án

```
UDM08_CHAT_PYTHON/
│
├── README.md
├── requirements.txt
├── .gitignore
├── client_main.py                  # Entry point: khởi động Eel, mở giao diện desktop app
│
├── database/
│   ├── schema.sql                  # Tạo bảng: users, messages, contacts, avatars...
│   └── seed_data.sql               # Dữ liệu mẫu để test
│
├── backend/
│   ├── __init__.py
│   ├── server_main.py              # Entry point: khởi động TCP server, accept connections
│   ├── message_protocol.py         # Định nghĩa format gói tin request/response (JSON)
│   │
│   ├── controllers/                # Nhận request từ client, gọi service tương ứng
│   │   ├── __init__.py
│   │   ├── auth_controller.py      # login, register, logout
│   │   ├── chat_controller.py      # send message, reply, forward
│   │   ├── contact_controller.py   # danh sách liên hệ, tìm kiếm user
│   │   └── profile_controller.py   # xem/cập nhật thông tin cá nhân, avatar
│   │
│   ├── services/                   # Business logic, xử lý nghiệp vụ
│   │   ├── __init__.py
│   │   ├── auth_service.py         # kiểm tra đăng nhập, hash password, tạo session
│   │   ├── chat_service.py         # xử lý logic reply/forward, broadcast tin nhắn
│   │   ├── contact_service.py      # logic liên hệ, trạng thái online/offline
│   │   └── profile_service.py      # logic cập nhật hồ sơ, upload avatar
│   │
│   ├── repositories/               # Tầng thao tác trực tiếp với database
│   │   ├── __init__.py
│   │   ├── user_repository.py      # CRUD bảng users
│   │   ├── message_repository.py   # CRUD bảng messages (reply_to_id, forward_from_id)
│   │   └── contact_repository.py   # CRUD bảng contacts
│   │
│   ├── models/                     # Entity/dataclass tương ứng bảng SQL
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── message.py
│   │   └── contact.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── db_connection.py        # Singleton kết nối SQLite/MySQL
│   │   ├── client_handler.py       # Thread xử lý từng client, đọc socket → gọi controller
│   │   ├── tcp_client_bridge.py    # Cầu nối giữa frontend và TCP socket (dùng Eel)
│   │   └── session_manager.py      # Quản lý các session/client đang kết nối
│   │
│   └── utils/
│       ├── __init__.py
│       ├── hash_utils.py           # Hash mật khẩu (bcrypt/hashlib)
│       └── validators.py           # Validate dữ liệu đầu vào
│
├── frontend/                       # Toàn bộ giao diện GUI (chạy trong Eel/webview)
│   ├── index.html                  # Trang login
│   ├── chat.html                   # Trang chat chính
│   ├── profile.html                # Trang thông tin cá nhân người dùng
│   │
│   ├── css/
│   │   ├── login.css
│   │   ├── chat.css
│   │   ├── sidebar.css
│   │   ├── profile.css
│   │   └── dark-mode.css
│   │
│   ├── js/
│   │   ├── login.js
│   │   ├── chat.js                 # Gửi/nhận tin nhắn, reply, forward
│   │   ├── sidebar.js              # Danh sách liên hệ, khu vực tin nhắn
│   │   ├── emoji-picker.js
│   │   ├── profile.js
│   │   ├── dark-mode.js
│   │   └── eel-bridge.js           # Gọi các hàm Python qua eel.xxx()
│   │
│   └── assets/
│       ├── avatars/                # Avatar mặc định + avatar người dùng upload
│       ├── emojis/
│       └── icons/
│
├── build/
│   └── build_app.py                # Script đóng gói bằng PyInstaller (.exe cài như Discord/Zalo)
│
└── docs/
    ├── architecture.png            # Sơ đồ kiến trúc client-server
    └── er_diagram.png              # Sơ đồ ER database
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
