-- ============================================================
-- UDM08_CHAT_PYTHON - Seed Data (SQLite)
-- Dữ liệu mẫu để test: users, conversations, messages, contacts...
-- Chạy SAU khi đã tạo schema.sql
-- ============================================================

PRAGMA foreign_keys = ON;


-- ============================================================
-- USERS (mật khẩu mẫu chỉ để test, KHÔNG dùng plain text thật)
-- password_hash bên dưới là placeholder, thực tế phải hash bằng
-- hash_utils.py (vd bcrypt/sha256) trước khi insert.
-- ============================================================
INSERT INTO users (username, password_hash, full_name, email, status) VALUES
('tai',    'HASHED_PASSWORD_1', 'Phan Tấn Tài',     'tai@example.com',    'online'),
('khai',   'HASHED_PASSWORD_2', 'Nguyễn Đức Khải',  'khai@example.com',   'offline'),
('hien',   'HASHED_PASSWORD_3', 'Hiển',             'hien@example.com',   'online'),
('cuong',  'HASHED_PASSWORD_4', 'Cường',            'cuong@example.com',  'away'),
('quyen',  'HASHED_PASSWORD_5', 'Huỳnh Thị Như Quyền', 'quyen@example.com', 'offline'),
('phat',   'HASHED_PASSWORD_6', 'Phát',             'phat@example.com',   'offline');


-- ============================================================
-- CONTACTS - quan hệ bạn bè
-- ============================================================
INSERT INTO contacts (user_id, contact_id, status) VALUES
(1, 2, 'accepted'),   -- tai <-> khai
(1, 3, 'accepted'),   -- tai <-> hien
(1, 4, 'pending'),    -- tai đã gửi lời mời tới cuong, chưa accept
(2, 3, 'accepted');   -- khai <-> hien


-- ============================================================
-- CONVERSATIONS
-- ============================================================
-- 1. Chat riêng (private) giữa tai (1) và khai (2)
INSERT INTO conversations (type, created_by) VALUES ('private', 1);   -- id = 1

-- 2. Nhóm "GR10 LTM"
INSERT INTO conversations (type, name, created_by) VALUES
('group', 'GR10 LTM', 1);                                             -- id = 2


-- ============================================================
-- CONVERSATION_MEMBERS
-- ============================================================
-- Conversation 1 (private: tai - khai)
INSERT INTO conversation_members (conversation_id, user_id, role) VALUES
(1, 1, 'member'),
(1, 2, 'member');

-- Conversation 2 (group: GR10 LTM) - 6 thành viên, tai là admin
INSERT INTO conversation_members (conversation_id, user_id, role) VALUES
(2, 1, 'admin'),
(2, 2, 'member'),
(2, 3, 'member'),
(2, 4, 'member'),
(2, 5, 'member'),
(2, 6, 'member');


-- ============================================================
-- MESSAGES
-- ============================================================
-- --- Trong conversation 1 (private tai - khai) ---
INSERT INTO messages (conversation_id, sender_id, message_type, content) VALUES
(1, 1, 'text', 'Chào Khải, tối nay làm phần protocol nha'),          -- id = 1
(1, 2, 'text', 'Ok để mình xem lại schema trước');                   -- id = 2

-- --- Trong conversation 2 (group GR10 LTM) ---
INSERT INTO messages (conversation_id, sender_id, message_type, content) VALUES
(2, 2, 'text', 'Cấu trúc dự án mọi người coi qua nha'),              -- id = 3
(2, 3, 'text', 'làm sao vậy mn'),                                    -- id = 4
(2, 4, 'text', 'Ông làm client network đi'),                         -- id = 5
(2, 1, 'text', 'ok để t làm protocol với sqlite trước');             -- id = 6

-- Tin nhắn reply (id=7 trả lời tin nhắn id=4 "làm sao vậy mn")
INSERT INTO messages (conversation_id, sender_id, message_type, content, reply_to_message_id) VALUES
(2, 1, 'text', 'lỗi kết nối thôi, mai fix', 4);                      -- id = 7

-- Tin nhắn ảnh (media, khớp media_service.py upload Cloudinary)
INSERT INTO messages (conversation_id, sender_id, message_type, media_url, media_name) VALUES
(2, 1, 'image',
 'https://res.cloudinary.com/demo/image/upload/v1/chat/sample_diagram.png',
 'sample_diagram.png');                                              -- id = 8

-- Tin nhắn đã bị thu hồi (is_deleted = 1) để test hiển thị "tin nhắn đã bị xóa"
INSERT INTO messages (conversation_id, sender_id, message_type, content, is_deleted) VALUES
(2, 4, 'text', 'test message sẽ xóa', 1);                            -- id = 9


-- ============================================================
-- MESSAGE_ATTACHMENTS (đính kèm thêm cho tin nhắn ảnh id=8)
-- ============================================================
INSERT INTO message_attachments (message_id, file_url, file_type, file_name) VALUES
(8, 'https://res.cloudinary.com/demo/image/upload/v1/chat/sample_diagram.png',
    'image', 'sample_diagram.png'),
(8, 'https://res.cloudinary.com/demo/image/upload/v1/chat/sample_diagram_2.png',
    'image', 'sample_diagram_2.png');


-- ============================================================
-- MESSAGE_STATUS - trạng thái đã đọc/nhận theo từng user
-- ============================================================
-- Tin nhắn id=6 trong group (2), các thành viên khác đã đọc
INSERT INTO message_status (message_id, user_id, status) VALUES
(6, 2, 'read'),
(6, 3, 'read'),
(6, 4, 'delivered'),   -- đã nhận nhưng chưa mở xem
(6, 5, 'sent'),        -- server đã gửi nhưng client chưa xác nhận nhận
(6, 6, 'sent');


-- ============================================================
-- MESSAGE_REACTIONS
-- ============================================================
INSERT INTO message_reactions (message_id, user_id, reaction_type) VALUES
(6, 3, 'like'),
(6, 4, 'like'),
(8, 2, 'love');


-- ============================================================
-- PINNED_MESSAGES
-- ============================================================
INSERT INTO pinned_messages (conversation_id, message_id, pinned_by) VALUES
(2, 3, 1);   -- tai ghim tin nhắn "Cấu trúc dự án mọi người coi qua nha"


-- ============================================================
-- NOTIFICATIONS
-- ============================================================
INSERT INTO notifications (user_id, type, content, related_user_id) VALUES
(4, 'friend_request', 'Phan Tấn Tài đã gửi lời mời kết bạn', 1),
(2, 'group_invite', 'Bạn đã được thêm vào nhóm GR10 LTM', 1);


-- ============================================================
-- USER_DEVICES + SESSIONS (test đăng nhập)
-- ============================================================
INSERT INTO user_devices (user_id, device_name, device_type, ip_address) VALUES
(1, 'Windows 11 - Client App', 'desktop', '192.168.1.10');           -- id = 1

INSERT INTO sessions (user_id, device_id, session_token, ip_address, expires_at) VALUES
(1, 1, 'SAMPLE_SESSION_TOKEN_ABC123', '192.168.1.10',
 datetime('now', '+7 days'));


-- ============================================================
-- CẬP NHẬT last_read_message_id cho conversation_members
-- (giúp tính unread count ở sidebar)
-- ============================================================
UPDATE conversation_members SET last_read_message_id = 6
    WHERE conversation_id = 2 AND user_id = 3;   -- hien đã đọc tới tin nhắn id 6

UPDATE conversation_members SET last_read_message_id = 2
    WHERE conversation_id = 1 AND user_id = 2;   -- khai đã đọc hết chat riêng