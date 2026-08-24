-- ============================================================
-- UDM08_CHAT_PYTHON - Seed Data (SQLite)
-- Dữ liệu mẫu để test:
-- users, contacts, conversations, conversation_members,
-- messages, message_status, message_attachments,
-- message_reactions, pinned_messages, notifications,
-- user_devices, sessions
--
-- Chạy SAU khi đã tạo schema.sql
-- ============================================================

PRAGMA foreign_keys = ON;


-- ============================================================
-- 1. USERS
-- ============================================================
-- Mật khẩu mẫu chỉ để test.
-- password_hash bên dưới là placeholder.
-- Khi đăng nhập thật, password phải được hash bằng hash_utils.py.

INSERT INTO users (
    username,
    password_hash,
    full_name,
    email,
    status
) VALUES
('tai',    'HASHED_PASSWORD_1', 'Phan Tấn Tài',        'tai@example.com',    'online'),
('khai',   'HASHED_PASSWORD_2', 'Nguyễn Đức Khải',     'khai@example.com',   'offline'),
('hien',   'HASHED_PASSWORD_3', 'Hiển',                'hien@example.com',   'online'),
('cuong',  'HASHED_PASSWORD_4', 'Cường',               'cuong@example.com',  'away'),
('quyen',  'HASHED_PASSWORD_5', 'Huỳnh Thị Như Quyền', 'quyen@example.com', 'offline'),
('phat',   'HASHED_PASSWORD_6', 'Phát',                'phat@example.com',   'offline');


-- ============================================================
-- 2. CONTACTS - QUAN HỆ KẾT BẠN
-- ============================================================
-- tai <-> khai: đã kết bạn
-- tai <-> hien: đã kết bạn
-- tai -> cuong: đang chờ
-- khai <-> hien: đã kết bạn

INSERT INTO contacts (
    user_id,
    contact_id,
    status
) VALUES
(1, 2, 'accepted'),
(1, 3, 'accepted'),
(1, 4, 'pending'),
(2, 3, 'accepted');


-- ============================================================
-- 3. CONVERSATIONS
-- ============================================================

-- ------------------------------------------------------------
-- 3.1. CHAT RIÊNG: Tài (1) <-> Khải (2)
-- ------------------------------------------------------------
-- private_user_1 và private_user_2 dùng để xác định
-- chính xác 2 người tham gia cuộc chat riêng.

INSERT INTO conversations (
    type,
    private_user_1,
    private_user_2,
    created_by
) VALUES (
    'private',
    1,
    2,
    1
);


-- ------------------------------------------------------------
-- 3.2. CHAT NHÓM: GR10 LTM
-- ------------------------------------------------------------

INSERT INTO conversations (
    type,
    name,
    created_by
) VALUES (
    'group',
    'GR10 LTM',
    1
);


-- ============================================================
-- 4. CONVERSATION_MEMBERS
-- ============================================================

-- ------------------------------------------------------------
-- 4.1. Chat riêng Tài - Khải
-- ------------------------------------------------------------

INSERT INTO conversation_members (
    conversation_id,
    user_id,
    role
) VALUES
(1, 1, 'member'),
(1, 2, 'member');


-- ------------------------------------------------------------
-- 4.2. Nhóm GR10 LTM - 6 thành viên
-- Tài là admin
-- ------------------------------------------------------------

INSERT INTO conversation_members (
    conversation_id,
    user_id,
    role
) VALUES
(2, 1, 'admin'),
(2, 2, 'member'),
(2, 3, 'member'),
(2, 4, 'member'),
(2, 5, 'member'),
(2, 6, 'member');


-- ============================================================
-- 5. MESSAGES
-- ============================================================

-- ------------------------------------------------------------
-- 5.1. Tin nhắn trong chat riêng Tài - Khải
-- ------------------------------------------------------------

INSERT INTO messages (
    conversation_id,
    sender_id,
    message_type,
    content
) VALUES
(
    1,
    1,
    'text',
    'Chào Khải, tối nay làm phần protocol nha'
),
(
    1,
    2,
    'text',
    'Ok để mình xem lại schema trước'
);


-- ------------------------------------------------------------
-- 5.2. Tin nhắn trong nhóm GR10 LTM
-- ------------------------------------------------------------

INSERT INTO messages (
    conversation_id,
    sender_id,
    message_type,
    content
) VALUES
(
    2,
    2,
    'text',
    'Cấu trúc dự án mọi người coi qua nha'
),
(
    2,
    3,
    'text',
    'làm sao vậy mn'
),
(
    2,
    4,
    'text',
    'Ông làm client network đi'
),
(
    2,
    1,
    'text',
    'ok để t làm protocol với sqlite trước'
);


-- ------------------------------------------------------------
-- 5.3. Tin nhắn reply
-- Tin nhắn này trả lời tin nhắn id = 4
-- ------------------------------------------------------------

INSERT INTO messages (
    conversation_id,
    sender_id,
    message_type,
    content,
    reply_to_message_id
) VALUES
(
    2,
    1,
    'text',
    'lỗi kết nối thôi, mai fix',
    4
);


-- ------------------------------------------------------------
-- 5.4. Tin nhắn hình ảnh
-- Khớp với media_service.py / Cloudinary
-- ------------------------------------------------------------

INSERT INTO messages (
    conversation_id,
    sender_id,
    message_type,
    media_url,
    media_name
) VALUES
(
    2,
    1,
    'image',
    'https://res.cloudinary.com/demo/image/upload/v1/chat/sample_diagram.png',
    'sample_diagram.png'
);


-- ------------------------------------------------------------
-- 5.5. Tin nhắn đã bị xóa
-- is_deleted = 1
-- ------------------------------------------------------------

INSERT INTO messages (
    conversation_id,
    sender_id,
    message_type,
    content,
    is_deleted
) VALUES
(
    2,
    4,
    'text',
    'test message sẽ xóa',
    1
);


-- ============================================================
-- 6. MESSAGE_ATTACHMENTS
-- ============================================================
-- Đính kèm thêm cho tin nhắn ảnh id = 8

INSERT INTO message_attachments (
    message_id,
    file_url,
    file_type,
    file_name
) VALUES
(
    8,
    'https://res.cloudinary.com/demo/image/upload/v1/chat/sample_diagram.png',
    'image',
    'sample_diagram.png'
),
(
    8,
    'https://res.cloudinary.com/demo/image/upload/v1/chat/sample_diagram_2.png',
    'image',
    'sample_diagram_2.png'
);


-- ============================================================
-- 7. MESSAGE_STATUS
-- ============================================================
-- Tin nhắn id = 6 trong nhóm.
-- Các thành viên khác có trạng thái khác nhau.

INSERT INTO message_status (
    message_id,
    user_id,
    status
) VALUES
(6, 2, 'read'),
(6, 3, 'read'),
(6, 4, 'delivered'),
(6, 5, 'sent'),
(6, 6, 'sent');


-- ============================================================
-- 8. MESSAGE_REACTIONS
-- ============================================================

INSERT INTO message_reactions (
    message_id,
    user_id,
    reaction_type
) VALUES
(6, 3, 'like'),
(6, 4, 'like'),
(8, 2, 'love');


-- ============================================================
-- 9. PINNED_MESSAGES
-- ============================================================
-- Tài ghim tin nhắn id = 3

INSERT INTO pinned_messages (
    conversation_id,
    message_id,
    pinned_by
) VALUES
(
    2,
    3,
    1
);


-- ============================================================
-- 10. NOTIFICATIONS
-- ============================================================

INSERT INTO notifications (
    user_id,
    type,
    content,
    related_user_id
) VALUES
(
    4,
    'friend_request',
    'Phan Tấn Tài đã gửi lời mời kết bạn',
    1
),
(
    2,
    'group_invite',
    'Bạn đã được thêm vào nhóm GR10 LTM',
    1
);


-- ============================================================
-- 11. USER_DEVICES
-- ============================================================

INSERT INTO user_devices (
    user_id,
    device_name,
    device_type,
    ip_address
) VALUES
(
    1,
    'Windows 11 - Client App',
    'desktop',
    '192.168.1.10'
);


-- ============================================================
-- 12. SESSIONS
-- ============================================================

INSERT INTO sessions (
    user_id,
    device_id,
    session_token,
    ip_address,
    expires_at
) VALUES
(
    1,
    1,
    'SAMPLE_SESSION_TOKEN_ABC123',
    '192.168.1.10',
    datetime('now', '+7 days')
);


-- ============================================================
-- 13. CẬP NHẬT LAST_READ_MESSAGE_ID
-- ============================================================

-- Hiển đã đọc tới tin nhắn id = 6 trong nhóm

UPDATE conversation_members
SET last_read_message_id = 6
WHERE conversation_id = 2
  AND user_id = 3;


-- Khải đã đọc hết chat riêng tới tin nhắn id = 2

UPDATE conversation_members
SET last_read_message_id = 2
WHERE conversation_id = 1
  AND user_id = 2;


-- ============================================================
-- KẾT THÚC SEED DATA
-- ============================================================