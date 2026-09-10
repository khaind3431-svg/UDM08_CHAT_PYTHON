from Code.backend.core.db_connection import db_cursor


def get_or_create_private_conversation(user_id_a: int, user_id_b: int) -> int:
    with db_cursor() as cur:
        cur.execute(
            """SELECT c.id FROM conversations c
               JOIN conversation_members m1 ON m1.conversation_id = c.id AND m1.user_id = ?
               JOIN conversation_members m2 ON m2.conversation_id = c.id AND m2.user_id = ?
               WHERE c.type = 'private'""",
            (user_id_a, user_id_b),
        )
        row = cur.fetchone()
        if row:
            return row["id"]

        cur.execute(
            "INSERT INTO conversations (type, created_by) VALUES ('private', ?)",
            (user_id_a,),
        )
        conversation_id = cur.lastrowid
        cur.executemany(
            "INSERT INTO conversation_members (conversation_id, user_id) VALUES (?, ?)",
            [(conversation_id, user_id_a), (conversation_id, user_id_b)],
        )
        return conversation_id


def save_message(conversation_id: int, sender_id: int, content=None,
                  reply_to_message_id=None, forward_from_message_id=None,
                  message_type: str = "text", media_url=None,
                  media_name=None, media_size=None) -> int:
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO messages
               (conversation_id, sender_id, content, reply_to_message_id,
                forward_from_message_id, message_type, media_url, media_name, media_size)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (conversation_id, sender_id, content, reply_to_message_id,
             forward_from_message_id, message_type, media_url, media_name, media_size),
        )
        return cur.lastrowid


def get_message_brief(message_id: int):
    with db_cursor() as cur:
        cur.execute(
            """SELECT m.id, m.content, m.conversation_id,
                      u.full_name AS sender_display, u.username AS sender_username
               FROM messages m JOIN users u ON u.id = m.sender_id
               WHERE m.id = ?""",
            (message_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "content": row["content"],
        "conversation_id": row["conversation_id"],
        "sender_display": row["sender_display"],
        "sender_username": row["sender_username"],
    }


def get_conversation_participants(conversation_id: int) -> list:
    """Danh sach username cua tat ca thanh vien trong 1 conversation -
    dung de biet REPLY/tin nhan can gui cho dung nhung ai."""
    with db_cursor() as cur:
        cur.execute(
            """SELECT u.username FROM conversation_members cm
               JOIN users u ON u.id = cm.user_id
               WHERE cm.conversation_id = ?""",
            (conversation_id,),
        )
        return [row["username"] for row in cur.fetchall()]


def get_conversation_history(conversation_id: int, limit: int = 200) -> list:
    with db_cursor() as cur:
        cur.execute(
            """SELECT m.id, u.username AS sender_username, m.content, m.created_at,
                      m.message_type, m.media_url, m.media_name
               FROM messages m
               JOIN users u ON u.id = m.sender_id
               WHERE m.conversation_id = ?
               ORDER BY m.id ASC
               LIMIT ?""",
            (conversation_id, limit),
        )
        return [
            {
                "id": row["id"],
                "sender": row["sender_username"],
                "content": row["content"] or "",
                "created_at": row["created_at"],
                "message_type": row["message_type"] or "text",
                "media_url": row["media_url"],
                "media_name": row["media_name"],
            }
            for row in cur.fetchall()
        ]