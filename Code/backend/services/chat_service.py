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


def save_message(conversation_id: int, sender_id: int, content: str,
                  reply_to_message_id=None, forward_from_message_id=None) -> int:
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO messages
               (conversation_id, sender_id, content, reply_to_message_id, forward_from_message_id)
               VALUES (?, ?, ?, ?, ?)""",
            (conversation_id, sender_id, content, reply_to_message_id, forward_from_message_id),
        )
        return cur.lastrowid


def get_message_brief(message_id: int):
    with db_cursor() as cur:
        cur.execute(
            """SELECT m.id, m.content, u.full_name AS sender_display
               FROM messages m JOIN users u ON u.id = m.sender_id
               WHERE m.id = ?""",
            (message_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {"id": row["id"], "content": row["content"], "sender_display": row["sender_display"]}