-- ============================================================
-- UDM08_CHAT_PYTHON - Database Schema (SQLite 3)
-- File DB đề xuất: database/chat.db
-- ============================================================

-- Bật ràng buộc khóa ngoại (SQLite mặc định TẮT, phải set mỗi
-- connection trong db_connection.py):
--   conn.execute("PRAGMA foreign_keys = ON")
PRAGMA foreign_keys = ON;

-- Bật WAL mode để cho phép đọc song song trong lúc đang ghi,
-- giảm nghẽn khi nhiều client thread cùng gửi tin nhắn:
PRAGMA journal_mode = WAL;


-- ============================================================
-- 1. USERS - Tài khoản người dùng
-- ============================================================
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    email           TEXT UNIQUE,
    phone           TEXT UNIQUE,
    avatar_url      TEXT DEFAULT NULL,
    bio             TEXT DEFAULT NULL,
    status          TEXT NOT NULL DEFAULT 'offline'
                    CHECK (status IN ('online', 'offline', 'away')),
    last_seen_at    TEXT DEFAULT NULL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_status ON users(status);

CREATE TRIGGER trg_users_updated_at
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = datetime('now') WHERE id = NEW.id;
END;


-- ============================================================
-- 2. CONVERSATIONS - Cuộc trò chuyện (1-1 hoặc nhóm)
-- ============================================================
CREATE TABLE conversations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    type            TEXT NOT NULL DEFAULT 'private'
                    CHECK (type IN ('private', 'group')),
    name            TEXT DEFAULT NULL,
    avatar_url      TEXT DEFAULT NULL,
    created_by      INTEGER NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_conversations_type ON conversations(type);

CREATE TRIGGER trg_conversations_updated_at
AFTER UPDATE ON conversations
BEGIN
    UPDATE conversations SET updated_at = datetime('now') WHERE id = NEW.id;
END;


-- ============================================================
-- 3. CONVERSATION_MEMBERS - Thành viên trong cuộc trò chuyện
-- ============================================================
CREATE TABLE conversation_members (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id         INTEGER NOT NULL,
    user_id                 INTEGER NOT NULL,
    role                    TEXT NOT NULL DEFAULT 'member'
                            CHECK (role IN ('member', 'admin')),
    nickname                TEXT DEFAULT NULL,
    is_muted                INTEGER NOT NULL DEFAULT 0,
    joined_at               TEXT NOT NULL DEFAULT (datetime('now')),
    last_read_message_id    INTEGER DEFAULT NULL,

    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (last_read_message_id) REFERENCES messages(id) ON DELETE SET NULL,
    UNIQUE (conversation_id, user_id)
);

CREATE INDEX idx_members_user ON conversation_members(user_id);


-- ============================================================
-- 4. MESSAGES - Tin nhắn
-- ============================================================
CREATE TABLE messages (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id             INTEGER NOT NULL,
    sender_id                   INTEGER NOT NULL,
    message_type                TEXT NOT NULL DEFAULT 'text'
                                CHECK (message_type IN
                                    ('text', 'image', 'file', 'emoji', 'system')),
    content                     TEXT DEFAULT NULL,
    media_url                   TEXT DEFAULT NULL,
    media_name                  TEXT DEFAULT NULL,
    media_size                  INTEGER DEFAULT NULL,

    reply_to_message_id         INTEGER DEFAULT NULL,
    forward_from_message_id     INTEGER DEFAULT NULL,

    is_edited                   INTEGER NOT NULL DEFAULT 0,
    is_deleted                  INTEGER NOT NULL DEFAULT 0,
    created_at                  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at                  TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reply_to_message_id) REFERENCES messages(id) ON DELETE SET NULL,
    FOREIGN KEY (forward_from_message_id) REFERENCES messages(id) ON DELETE SET NULL
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_sender ON messages(sender_id);

CREATE TRIGGER trg_messages_updated_at
AFTER UPDATE ON messages
BEGIN
    UPDATE messages SET updated_at = datetime('now') WHERE id = NEW.id;
END;


-- ============================================================
-- 5. MESSAGE_STATUS - Trạng thái gửi/nhận/đọc theo từng user
-- ============================================================
CREATE TABLE message_status (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'sent'
                    CHECK (status IN ('sent', 'delivered', 'read')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (message_id, user_id)
);

CREATE INDEX idx_status_user ON message_status(user_id, status);

CREATE TRIGGER trg_message_status_updated_at
AFTER UPDATE ON message_status
BEGIN
    UPDATE message_status SET updated_at = datetime('now') WHERE id = NEW.id;
END;


-- ============================================================
-- 6. CONTACTS - Danh bạ / kết bạn / chặn
-- ============================================================
CREATE TABLE contacts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    contact_id      INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'accepted', 'blocked', 'rejected')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user_id, contact_id),
    CHECK (user_id <> contact_id)
);

CREATE INDEX idx_contacts_status ON contacts(status);

CREATE TRIGGER trg_contacts_updated_at
AFTER UPDATE ON contacts
BEGIN
    UPDATE contacts SET updated_at = datetime('now') WHERE id = NEW.id;
END;


-- ============================================================
-- 7. USER_DEVICES - Thiết bị đăng nhập
-- ============================================================
CREATE TABLE user_devices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    device_name     TEXT DEFAULT NULL,
    device_type     TEXT NOT NULL DEFAULT 'desktop'
                    CHECK (device_type IN ('desktop', 'mobile', 'web')),
    ip_address      TEXT DEFAULT NULL,
    last_active_at  TEXT NOT NULL DEFAULT (datetime('now')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_devices_user ON user_devices(user_id);


-- ============================================================
-- 8. SESSIONS - Phiên đăng nhập / token xác thực
-- ============================================================
CREATE TABLE sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    device_id       INTEGER DEFAULT NULL,
    session_token   TEXT NOT NULL UNIQUE,
    ip_address      TEXT DEFAULT NULL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    expires_at      TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES user_devices(id) ON DELETE SET NULL
);

CREATE INDEX idx_sessions_token ON sessions(session_token);
CREATE INDEX idx_sessions_user ON sessions(user_id, is_active);


-- ============================================================
-- 9. MESSAGE_ATTACHMENTS - Nhiều file đính kèm cho 1 tin nhắn
-- ============================================================
CREATE TABLE message_attachments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      INTEGER NOT NULL,
    file_url        TEXT NOT NULL,
    file_type       TEXT NOT NULL DEFAULT 'other'
                    CHECK (file_type IN ('image', 'video', 'audio', 'document', 'other')),
    file_name       TEXT DEFAULT NULL,
    file_size       INTEGER DEFAULT NULL,
    thumbnail_url   TEXT DEFAULT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);

CREATE INDEX idx_attachments_message ON message_attachments(message_id);


-- ============================================================
-- 10. MESSAGE_REACTIONS - Thả cảm xúc vào tin nhắn
-- ============================================================
CREATE TABLE message_reactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    reaction_type   TEXT NOT NULL DEFAULT 'like',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (message_id, user_id)
);

CREATE INDEX idx_reactions_message ON message_reactions(message_id);


-- ============================================================
-- 11. PINNED_MESSAGES - Tin nhắn được ghim
-- ============================================================
CREATE TABLE pinned_messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    message_id      INTEGER NOT NULL,
    pinned_by       INTEGER NOT NULL,
    pinned_at       TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (pinned_by) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (conversation_id, message_id)
);


-- ============================================================
-- 12. MESSAGE_DELETIONS - Xóa tin nhắn "chỉ ở phía tôi"
-- ============================================================
CREATE TABLE message_deletions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    deleted_at      TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (message_id, user_id)
);


-- ============================================================
-- 13. NOTIFICATIONS - Thông báo hệ thống
-- ============================================================
CREATE TABLE notifications (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                     INTEGER NOT NULL,
    type                        TEXT NOT NULL DEFAULT 'system'
                                CHECK (type IN
                                    ('friend_request', 'friend_accepted', 'group_invite',
                                     'mention', 'message', 'system')),
    content                     TEXT NOT NULL,
    related_user_id             INTEGER DEFAULT NULL,
    related_conversation_id     INTEGER DEFAULT NULL,
    related_message_id          INTEGER DEFAULT NULL,
    is_read                     INTEGER NOT NULL DEFAULT 0,
    created_at                  TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (related_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (related_conversation_id) REFERENCES conversations(id) ON DELETE SET NULL,
    FOREIGN KEY (related_message_id) REFERENCES messages(id) ON DELETE SET NULL
);

CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);


-- ============================================================
-- GHI CHÚ THIẾT KẾ (SQLite)
-- ============================================================
-- 1. datetime('now') trả về giờ UTC. Nếu muốn giờ VN khi hiển thị,
--    xử lý ở tầng Python (datetime + timedelta(hours=7)) thay vì
--    lưu giờ local trong DB — tránh lệch giờ khi so sánh/sắp xếp.
--
-- 2. Mỗi bảng có updated_at đều có TRIGGER riêng để tự cập nhật,
--    vì SQLite không hỗ trợ "ON UPDATE CURRENT_TIMESTAMP" như MySQL.
--
-- 3. BẮT BUỘC bật "PRAGMA foreign_keys = ON" ở MỖI connection mới
--    trong db_connection.py, vì SQLite mặc định tắt ràng buộc FK:
--
--      import sqlite3
--      conn = sqlite3.connect("database/chat.db", check_same_thread=False)
--      conn.execute("PRAGMA foreign_keys = ON")
--
-- 4. Với nhiều thread cùng ghi (client_handler.py chạy thread/client),
--    nên dùng 1 Lock() riêng khi INSERT/UPDATE để tránh lỗi
--    "database is locked", dù đã bật WAL mode:
--
--      import threading
--      db_lock = threading.Lock()
--      with db_lock:
--          cursor.execute("INSERT INTO messages ...")
--          conn.commit()
--
-- 5. File chat.db nên đặt trong database/, thêm vào .gitignore
--    nếu không muốn commit dữ liệu thật lên git (chỉ commit
--    schema.sql + seed_data.sql).