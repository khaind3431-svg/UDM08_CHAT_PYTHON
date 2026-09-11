-- ============================================================
-- UDM08_CHAT_PYTHON - Seed Data (SQLite)
-- Du lieu mau de test, khop dung voi schema.sql hien tai
-- (chi con 5 bang: users, conversations, conversation_members,
--  messages, contacts).
--
-- Chay SAU khi da tao schema.sql:
--   sqlite3 Code/database/chat.db < Code/database/schema.sql
--   sqlite3 Code/database/chat.db < Code/database/seed_data.sql
-- ============================================================

PRAGMA foreign_keys = ON;


-- ============================================================
-- 1. USERS
-- ============================================================
-- password_hash ben duoi la placeholder, KHONG phai hash that.
-- Khi dang ky/dang nhap that qua GUI, mat khau duoc hash bang
-- Code/backend/utils/hash_utils.py (salt ngau nhien + SHA-256).
-- Neu muon dang nhap thu voi du lieu seed nay, hay dang ky 1 tai
-- khoan moi qua man hinh Dang ky thay vi dung mat khau mau o day.

INSERT INTO users (
    username, password_hash, full_name, status
) VALUES
('tai',   'PLACEHOLDER_HASH_KHONG_DUNG_DE_DANG_NHAP', 'Phan Tấn Tài',       'offline'),
('khai',  'PLACEHOLDER_HASH_KHONG_DUNG_DE_DANG_NHAP', 'Nguyễn Đức Khải',    'offline'),
('hien',  'PLACEHOLDER_HASH_KHONG_DUNG_DE_DANG_NHAP', 'Nguyễn Hồ Minh Hiển','offline'),
('cuong', 'PLACEHOLDER_HASH_KHONG_DUNG_DE_DANG_NHAP', 'Phan Triều Cường',   'offline');


-- ============================================================
-- 2. CONTACTS - quan he ket ban
-- ============================================================
-- tai  <-> khai : da ket ban (accepted)
-- tai  <-> hien : da ket ban (accepted)
-- tai  ->  cuong: dang cho phan hoi (pending)

INSERT INTO contacts (user_id, contact_id, status) VALUES
(1, 2, 'accepted'),
(1, 3, 'accepted'),
(1, 4, 'pending');


-- ============================================================
-- 3. CONVERSATIONS - chi demo chat rieng (khong dung chat nhom)
-- ============================================================
-- Cap user cho 1 cuoc tro chuyen 'private' duoc xac dinh qua
-- bang conversation_members (2 dong cung conversation_id), KHONG
-- luu truc tiep tren conversations - xem
-- chat_service.get_or_create_private_conversation().

-- 3.1. Chat rieng: tai (1) <-> khai (2)
INSERT INTO conversations (type, created_by) VALUES ('private', 1);

-- 3.2. Chat rieng: tai (1) <-> hien (3)
INSERT INTO conversations (type, created_by) VALUES ('private', 1);


-- ============================================================
-- 4. CONVERSATION_MEMBERS
-- ============================================================

-- 4.1. Conversation 1 (tai - khai)
INSERT INTO conversation_members (conversation_id, user_id) VALUES
(1, 1),
(1, 2);

-- 4.2. Conversation 2 (tai - hien)
INSERT INTO conversation_members (conversation_id, user_id) VALUES
(2, 1),
(2, 3);


-- ============================================================
-- 5. MESSAGES
-- ============================================================

-- 5.1. Tin nhan van ban trong conversation 1 (tai - khai)
INSERT INTO messages (conversation_id, sender_id, message_type, content) VALUES
(1, 1, 'text', 'Chào Khải, tối nay làm phần protocol nha'),
(1, 2, 'text', 'Ok để mình xem lại schema trước');

-- 5.2. Tin nhan reply - tra loi tin nhan id = 2 (cau "Ok de minh...")
INSERT INTO messages (
    conversation_id, sender_id, message_type, content, reply_to_message_id
) VALUES
(1, 1, 'text', 'Ok, xong nhắn mình nhé', 2);

-- 5.3. Tin nhan hinh anh - luu cuc bo trong Code/uploads/, KHONG
-- dung dich vu ngoai (Cloudinary...). media_url la ten file da
-- luu tren dia server, khop dung voi media_service.save_image().
INSERT INTO messages (
    conversation_id, sender_id, message_type, media_url, media_name, media_size
) VALUES
(1, 1, 'image', 'sample_diagram_a1b2c3d4e5f6.png', 'sample_diagram.png', 204800);

-- 5.4. Tin nhan forward - chuyen tiep tin nhan id = 1 sang
-- conversation 2 (tai gui lai cho hien)
INSERT INTO messages (
    conversation_id, sender_id, message_type, content, forward_from_message_id
) VALUES
(2, 1, 'text', 'Chào Khải, tối nay làm phần protocol nha', 1);

-- 5.5. Tin nhan van ban khac trong conversation 2 (tai - hien)
INSERT INTO messages (conversation_id, sender_id, message_type, content) VALUES
(2, 3, 'text', 'Ok để t xem thử');


-- ============================================================
-- KET THUC SEED DATA
-- ============================================================