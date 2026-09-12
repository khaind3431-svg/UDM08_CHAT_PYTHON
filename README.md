# UDM08_CHAT_PYTHON — Chat TCP Client-Server

- **Mã đề tài**: UDM_08
- **Tên đề tài**: Chat TCP Client–Server
- **Mô tả**: Ứng dụng chat client–server qua TCP, toàn bộ thao tác thực hiện qua GUI (đăng ký/đăng nhập, chat riêng, kết bạn, gửi ảnh, reply/forward tin nhắn, xem lại lịch sử chat).
- **Video demo**: `<điền link video sau khi quay demo>`

## Danh sách thành viên

> Điền đầy đủ Họ tên và MSSV thật trước khi nộp — bảng dưới đã đối chiếu kỹ với lịch sử commit trên nhánh `main` (không tính các nhánh `feature/*` chưa merge).

| Họ và tên | MSSV | Tài khoản GitHub | Phụ trách chính |
|---|---|---|---|
| _Phan Triều Cường_ | _(034205002849)_ | PhanTrieuCuong123 | Xác thực (đăng ký/đặng nhập), GUI, avatar, IP/Port, sửa lỗi tổng hợp xuyên suốt dự án |
| _Phan Tấn Tài_ | _(082206015321)_ | phantantai08 | Database (schema, ERD, seed data), giao thức, migration hồ sơ người dùng |
| _Nguyễn Đức Khải_ | _(075206003431)_ | Nguyen Duc Khai | Server core ban đầu, tổ chức lại cấu trúc thư mục dự án, README |
| _Trần Thanh Hải_ | _(077205001506)_ | seward1812 | `client_manager.py` / `client_handler.py` (quản lý kết nối client) |
| _Nguyễn Hồ Minh Hiển_ | _(083206009387)_ | hienminhhonguyen | Module chat riêng (private chat), test tự động, tài liệu deploy, tính năng gửi ảnh |
| _Nguyễn Võ Tấn Phát_ | _(082206004751)_ | Nguyễn Võ Tấn Phát | Code phía client theo cấu trúc dự án chung, hoàn thiện tính năng kết bạn |

## Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Giao tiếp mạng cốt lõi | Python `socket` (TCP thuần) + `threading` (1 thread/client) |
| Giao thức | Text packet tự định nghĩa, mỗi packet kết thúc bằng `\n`, các trường phân tách bằng `\|` |
| Giao diện Client | HTML/CSS/JavaScript, đóng gói thành ứng dụng desktop bằng **pywebview** |
| Cơ sở dữ liệu | **SQLite 3** (file `Code/database/chat.db`) |
| Mã hoá mật khẩu | SHA-256 + salt ngẫu nhiên mỗi user (`Code/backend/utils/hash_utils.py`) — không lưu mật khẩu dạng plaintext |
| Lưu trữ ảnh chat | Lưu file cục bộ trên máy Server tại `Code/uploads/` |

### Vì sao dùng pywebview thay vì Web App

`pywebview` chỉ dùng để **hiển thị giao diện** (bọc HTML/CSS/JS có sẵn vào 1 cửa sổ desktop native), **không phải Web App** theo nghĩa bị cấm trong yêu cầu đề tài:

- Toàn bộ giao tiếp mạng cốt lõi giữa Client và Server vẫn là **socket TCP thuần**, không đi qua HTTP/WebSocket.
- Ứng dụng chạy như 1 chương trình desktop độc lập, không cần mở trình duyệt để sử dụng.
- Đã được giảng viên xác nhận đồng ý cho dùng, với điều kiện không dùng WebSocket (dự án này không sử dụng WebSocket ở bất kỳ đâu).

## Yêu cầu môi trường

- Python 3.10 trở lên
- Cài thư viện:
```bash
  pip install -r requirements.txt
```

## Cấu hình

| Nơi cấu hình | Ý nghĩa |
|---|---|
| `Code/config/server_config.py` | Host/port mặc định của server, timeout kết nối, mã hoá ký tự (`ENCODING`) |
| `Code/config/db_config.py` | Đường dẫn tới file database SQLite (`chat.db`) |

IP/Port **không bị hard-code cố định cho 1 máy** — phía Client cho phép nhập IP/Port của Server ngay ở màn hình đăng nhập, không bắt buộc phải sửa code khi đổi máy chạy server.

## Cách chạy

### 1. Khởi tạo database (chỉ cần làm 1 lần, hoặc khi muốn làm mới dữ liệu)

```bash
sqlite3 Code/database/chat.db < Code/database/schema.sql
sqlite3 Code/database/chat.db < Code/database/seed_data.sql   # tuỳ chọn: nạp dữ liệu mẫu để test nhanh
```

> Xem thêm ghi chú về `chat.db` ở mục **Lưu ý quan trọng** bên dưới.

### 2. Chạy Server

```bash
python -m Code.backend.server_main
```

Server lắng nghe theo cấu hình trong `Code/config/server_config.py` (mặc định `0.0.0.0`).

### 3. Chạy Client (GUI desktop)

```bash
python Code/client/gui_client.py
```

Ở màn hình đăng nhập, nhập đúng IP/Port của máy đang chạy Server để kết nối (có thể là `127.0.0.1` nếu chạy thử trên cùng 1 máy, hoặc IP LAN thật nếu demo trên 2 máy khác nhau).

## Giao thức (Protocol)

Client và Server trao đổi bằng các packet dạng text, mỗi packet kết thúc bằng `\n`, các trường ngăn cách bằng `|`.

**Loại packet Client gửi lên Server:**

```
LOGIN | REGISTER | LOGOUT | PING
MESSAGE | PRIVATE | REPLY | FORWARD | IMAGE
ADDFRIEND | FRIEND_RESP | FRIENDLIST | FRIENDREQUESTS
GETINFO | UPDATEPROFILE | UPDATEAVATAR | GETHISTORY
```

Server phản hồi tương ứng bằng các packet cùng loại (ví dụ `PRIVATE|...`, `REPLY|...`) hoặc `ERROR|<lý do>` khi dữ liệu không hợp lệ.

## Cấu trúc thư mục

```text
UDM08_CHAT_PYTHON/
├── README.md
├── requirements.txt
├── .gitignore
├── DOCX/                          # Báo cáo (Word)
├── PPTX/                          # Slide thuyết trình
├── Extra/
│   └── DEPLOY.md
└── Code/
    ├── backend/
    │   ├── server_main.py         # Entry point: accept loop, quản lý thread/client
    │   ├── message_protocol.py    # Router phân loại packet theo loại
    │   ├── controllers/           # Xử lý nghiệp vụ theo loại packet
    │   │   ├── auth_controller.py
    │   │   ├── chat_controller.py
    │   │   ├── contact_controller.py
    │   │   └── profile_controller.py
    │   ├── core/                  # Thành phần lõi của server
    │   │   ├── client_handler.py      # Vòng lặp xử lý 1 client (1 thread)
    │   │   ├── client_manager.py      # Quản lý danh sách kết nối đang online
    │   │   ├── session_manager.py     # Trạng thái online, broadcast danh sách online
    │   │   └── db_connection.py       # Kết nối SQLite
    │   ├── services/              # Logic nghiệp vụ + truy vấn DB
    │   │   ├── auth_service.py
    │   │   ├── broadcast_service.py
    │   │   ├── chat_service.py
    │   │   ├── contact_service.py
    │   │   ├── media_service.py
    │   │   ├── private_chat_service.py
    │   │   └── profile_service.py
    │   └── utils/
    │       ├── hash_utils.py
    │       ├── server_logger.py
    │       └── validators.py
    ├── client/
    │   └── gui_client.py          # Client desktop (pywebview + socket TCP)
    ├── config/
    │   ├── db_config.py
    │   └── server_config.py
    ├── database/
    │   ├── schema.sql             # Cấu trúc 5 bảng: users, conversations,
    │   │                          # conversation_members, messages, contacts
    │   ├── seed_data.sql          # Dữ liệu mẫu để test nhanh
    │   └── chat.db                # (không commit — xem Lưu ý quan trọng)
    ├── uploads/                   # Ảnh chat lưu tại đây (không commit)
    └── frontend/
        ├── chat.html
        ├── login.html
        ├── css/
        └── js/
            ├── network.js         # Parse packet Server gửi về
            ├── login-network.js
            ├── chat-network.js
            ├── chat-avatar.js
            ├── chat-history.js
            ├── theme-toggle.js
            └── ui-interactions.js
```

## Lưu ý quan trọng

**1. File `Code/database/chat.db` không được commit lên Git**
Đây là dữ liệu runtime (tài khoản/tin nhắn thật sinh ra lúc chạy/test), không phải mã nguồn, đã được thêm vào `.gitignore`. Muốn có database để chạy thử, tạo lại bằng lệnh ở mục **Cách chạy** phía trên (`schema.sql` + `seed_data.sql`).

**2. File `Code/uploads/` (ảnh gửi trong chat) cũng không commit**
Server tự tạo lại thư mục này khi có ảnh đầu tiên được gửi lên (`media_service.py` gọi `mkdir(parents=True, exist_ok=True)`), không cần tạo tay.

**3. Các thư mục `__pycache__/` và file `.pyc`**
Đây là bytecode Python được tự sinh ra mỗi khi chạy `python ...`, dùng để chạy lại nhanh hơn ở lần sau — **không phải mã nguồn**, không ai viết tay, và không ảnh hưởng tới chương trình nếu xoá đi (sẽ tự sinh lại). Đã được `.gitignore` bỏ qua, không cần quan tâm khi đọc code.

**4. Về Database**: chỉ dùng **SQLite** (file đơn `chat.db`, không cần cài đặt server DB rời như MySQL/PostgreSQL). Toàn bộ câu lệnh SQL raw, không dùng ORM.

## Phạm vi và giới hạn

- Đã hoàn thành: đăng ký/đăng nhập, chat riêng (1-1), kết bạn, gửi/nhận ảnh, reply, forward, xem avatar, chọn/gửi/hiển thị emoji, xem lại lịch sử chat.
- Chưa hỗ trợ: chat nhóm (group chat) qua giao diện — dù backend có sẵn cơ chế broadcast, hiện chưa có nút bấm tương ứng trên GUI; chỉnh sửa/thu hồi tin nhắn đã gửi; thông báo đẩy (push notification).
