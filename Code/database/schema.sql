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
    avatar_url      TEXT DEFAULT NULL,
    bio             TEXT DEFAULT NULL,
    gender          TEXT DEFAULT NULL
                    CHECK (gender IN ('male', 'female', 'other') OR gender IS NULL),
    birthday        TEXT DEFAULT NULL,
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

-- Ghi chu: cap user cho 1 cuoc tro chuyen 'private' duoc xac dinh
-- qua bang conversation_members (2 dong voi cung conversation_id),
-- xem chat_service.get_or_create_private_conversation(). Rang buoc
-- "moi cap user chi co 1 cuoc tro chuyen rieng" duoc dam bao o tang
-- ung dung (Python), khong phai o tang DB.

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
    joined_at               TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
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
-- 5. CONTACTS - Danh bạ / kết bạn / chặn
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

-- Không cho cùng một cặp user tạo quan hệ A->B và B->A trùng nhau.
CREATE UNIQUE INDEX idx_contacts_unique_pair
    ON contacts(
        MIN(user_id, contact_id),
        MAX(user_id, contact_id)
    );

CREATE TRIGGER trg_contacts_updated_at
AFTER UPDATE ON contacts
BEGIN
    UPDATE contacts SET updated_at = datetime('now') WHERE id = NEW.id;
END;
