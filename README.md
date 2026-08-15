# UDM_08 — Chat TCP Client-Server

Ứng dụng chat client-server qua TCP, toàn bộ thao tác thực hiện bằng GUI.

## 🛠 Công nghệ sử dụng

- **Giao tiếp real-time:** Python `socket` (TCP), threading để xử lý nhiều client
- **Backend:** Python (kiến trúc Controller – Service – Repository)
- **Frontend:** HTML/CSS/JS, nhúng vào app desktop qua **Eel**
- **Database:** MySQL (dữ liệu user, message, contact có quan hệ rõ ràng, dùng JOIN để lấy tin nhắn kèm người gửi/tin được reply)
- **Lưu trữ ảnh (avatar + ảnh chat):** Cloudinary (object storage, free tier) — ảnh không lưu trong MySQL, chỉ lưu URL
- **Đóng gói ứng dụng:** PyInstaller → file `.exe` cài đặt như Discord/Zalo
- **Deploy server:** VPS (Oracle Cloud / Google Cloud Free Tier), chạy nền bằng `systemd`

## 📁 Cấu trúc dự án

## 📁 Cấu trúc dự án

```text
UDM08_CHAT_PYTHON/
│
├── README.md
├── requirements.txt
├── .gitignore
├── client_main.py                  # Entry point client, kết nối tới SERVER_HOST cố định
│
├── config/
│   ├── server_config.py            # SERVER_HOST, SERVER_PORT (TCP)
│   ├── db_config.py                # MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB
│   └── cloudinary_config.py        # CLOUD_NAME, API_KEY, API_SECRET
│
├── database/
│   ├── schema.sql                  # users, messages, conversations, contacts (MySQL)
│   └── seed_data.sql
│
├── backend/                        # Chạy trên VPS
│   ├── __init__.py
│   ├── server_main.py              # Khởi động TCP server, accept connections
│   ├── message_protocol.py         # Format gói tin request/response (JSON)
│   │
│   ├── controllers/
│   │   ├── auth_controller.py
│   │   ├── chat_controller.py
│   │   ├── contact_controller.py
│   │   └── profile_controller.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── chat_service.py         # Reply/forward, broadcast tin nhắn
│   │   ├── contact_service.py
│   │   ├── profile_service.py
│   │   └── media_service.py        # Upload ảnh lên Cloudinary, trả về URL
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   ├── message_repository.py
│   │   └── contact_repository.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── message.py
│   │   └── contact.py
│   │
│   ├── core/
│   │   ├── db_connection.py        # Kết nối MySQL
│   │   ├── client_handler.py       # Thread xử lý từng client qua TCP
│   │   └── session_manager.py
│   │
│   └── utils/
│       ├── hash_utils.py
│       └── validators.py
│
├── frontend/                       # Giao diện GUI (Eel/webview)
│   ├── index.html                  # Login
│   ├── chat.html                   # Chat chính
│   ├── profile.html                # Thông tin cá nhân
│   │
│   ├── css/
│   │   ├── login.css
│   │   ├── chat.css
│   │   ├── sidebar.css
│   │   ├── profile.css
│   │   └── dark-mode.css
│   │
│   └── js/
│       ├── login.js
│       ├── chat.js                 # Gửi/nhận, reply, forward
│       ├── sidebar.js
│       ├── emoji-picker.js
│       ├── profile.js
│       ├── dark-mode.js
│       └── eel-bridge.js           # Gọi hàm Python qua eel.xxx()
│
├── deploy/
│   ├── server_setup.sh             # Cài Python, MySQL, dependencies trên VPS
│   └── chatserver.service          # systemd — giữ server chạy nền, tự restart
│
├── build/
│   └── build_app.py                # PyInstaller đóng gói client thành .exe
│
└── docs/
    ├── architecture.png
    └── er_diagram.png
```

## 🚀 Cách deploy (mô hình giống Discord/Zalo)

1. Thuê/tạo 1 VPS (vd: Oracle Cloud Free Tier), cài Python + MySQL bằng `deploy/server_setup.sh`
2. Chạy `backend/server_main.py` trên VPS, dùng `deploy/chatserver.service` để server tự khởi động lại nếu crash hoặc VPS reboot
3. Mở port TCP (vd: `5555`) trên firewall VPS
4. Trong `config/server_config.py` của client, ghi sẵn IP/domain của VPS
5. Đóng gói client bằng `build/build_app.py` (PyInstaller) → ra file `.exe`
6. Người dùng chỉ cần tải `.exe` về, mở lên là tự kết nối vào server qua TCP — không cần cài Python, không cần biết địa chỉ server

## 🖼 Lưu trữ ảnh (avatar + ảnh trong đoạn chat)

- Ảnh **không lưu trong MySQL** và **không lưu trực tiếp trên VPS**
- Luồng xử lý: Client chọn ảnh → gửi qua TCP tới server → server (`media_service.py`) upload ảnh lên **Cloudinary** → nhận về URL công khai → lưu URL đó vào MySQL (`avatar_url` trong bảng `users`, `attachment_url` trong bảng `messages`)
- Client tải/hiển thị ảnh bằng cách load trực tiếp từ URL Cloudinary (qua HTTP), không cần đi qua TCP server → giảm tải cho server chat

## ⚠️ Lưu ý

- TCP vẫn là giao thức chính cho toàn bộ chat real-time (đúng yêu cầu đề bài) — Cloudinary/HTTP chỉ dùng riêng cho việc tải ảnh
- Phần deploy VPS + Cloudinary là mở rộng thêm ngoài yêu cầu tối thiểu của đề — nên xác nhận với giảng viên nếu muốn được tính điểm cộng cho phần này