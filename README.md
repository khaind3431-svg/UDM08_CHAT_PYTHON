# UDM08_CHAT_PYTHON - Chat TCP Client-Server

Du an chat client-server bang Python socket TCP, gom server TCP, giao dien HTML/CSS/JS va bo schema SQLite de phat trien cac chuc nang tai khoan, danh ba, hoi thoai va tin nhan.

## Cong nghe su dung

- Backend: Python `socket`, `threading`
- Protocol: text packet qua TCP, moi packet ket thuc bang `\n`
- Frontend: HTML/CSS/JavaScript tinh trong `Code/frontend`
- Database: SQLite 3, schema va seed data trong `Code/database`
- Cau hinh: cac hang so server trong `Code/config/server_config.py`

## Cau truc du an hien tai

```text
UDM08_CHAT_PYTHON/
├── README.md
├── Extra/
│   └── DEPLOY.md
└── Code/
    ├── backend/
    │   ├── __init__.py
    │   ├── server_main.py              # Entry point TCP server
    │   ├── message_protocol.py         # Parse/validate packet LOGIN, MESSAGE, PRIVATE...
    │   ├── controllers/
    │   │   ├── auth_controller.py
    │   │   ├── chat_controller.py
    │   │   ├── contact_controller.py
    │   │   └── profile_controller.py
    │   ├── core/
    │   │   ├── client_handler.py
    │   │   ├── db_connection.py
    │   │   └── session_manager.py
    │   ├── models/
    │   │   ├── contact.py
    │   │   ├── message.py
    │   │   └── user.py
    │   ├── repositories/
    │   │   ├── contact_repository.py
    │   │   ├── message_repository.py
    │   │   └── user_repository.py
    │   ├── services/
    │   │   ├── auth_service.py
    │   │   ├── broadcaster.py
    │   │   ├── chat_service.py
    │   │   ├── contact_service.py
    │   │   ├── media_service.py
    │   │   ├── private_chat.py
    │   │   └── profile_service.py
    │   └── utils/
    │       ├── hash_utils.py
    │       ├── server_logger.py
    │       └── validators.py
    ├── config/
    │   ├── cloudinary_config.py
    │   ├── db_config.py
    │   └── server_config.py
    ├── database/
    │   ├── schema.sql
    │   └── seed_data.sql
    └── frontend/
        ├── chat.html
        ├── login.html
        ├── css/
        │   ├── base.css
        │   ├── chat.css
        │   ├── login.css
        │   ├── sidebar.css
        │   └── theme.css
        └── js/
            ├── theme-toggle.js
            └── ui-interactions.js
```

## Chay server TCP

Yeu cau: Python 3.10 tro len.

Chay tu thu muc goc du an:

```bash
python Code/backend/server_main.py
```

Hoac chay theo module:

```bash
python -m Code.backend.server_main
```

Mac dinh server listen tai:

- Host: `0.0.0.0`
- Port: `5000`

Co the doi cac gia tri nay trong `Code/config/server_config.py`.

## Protocol TCP hien co

Client gui packet dang text, ket thuc moi packet bang newline `\n`.

```text
LOGIN|username
MESSAGE|noi dung
PRIVATE|nguoi_nhan|noi dung
PING
LOGOUT
```

Server tra ve:

```text
SYSTEM|noi dung
ONLINE|user1,user2
MESSAGE|sender|noi dung
PRIVATE|sender|noi dung
PONG
ERROR|noi dung
```

## Kiem tra nhanh bang terminal

Mo terminal 1 de chay server:

```bash
python Code/backend/server_main.py
```

Mo terminal 2 de ket noi thu bang `nc`:

```bash
nc 127.0.0.1 5000
```

Sau do nhap:

```text
LOGIN|tai
MESSAGE|Xin chao moi nguoi
PING
```

## Database

Schema SQLite nam trong:

```text
Code/database/schema.sql
Code/database/seed_data.sql
```

Tao database mau:

```bash
mkdir -p database
sqlite3 database/chat.db < Code/database/schema.sql
sqlite3 database/chat.db < Code/database/seed_data.sql
```

Luu y: cac module repository/service lien quan database hien moi la khung file, chua co logic ket noi day du. Server TCP hien tai dang quan ly user online trong bo nho runtime.

## Trang thai hien tai

- `Code/backend/server_main.py` la phan server TCP dang co logic chinh.
- `Code/frontend/login.html` va `Code/frontend/chat.html` la giao dien tinh/demo UI, chua ket noi truc tiep den TCP server.
- Nhieu file trong `controllers`, `services`, `repositories`, `models`, `core` dang la file khung de tiep tuc phat trien.
- Repo hien chua co `requirements.txt`, `Dockerfile`, script PyInstaller hoac file `systemd` deploy.
