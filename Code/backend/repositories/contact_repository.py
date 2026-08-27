"""
contact_repository.py - Truy van du lieu tho cho bang `contacts`.

Quy uoc 1 dong trong bang contacts (user_id, contact_id, status):
    (A, B, 'pending')   -> A da gui loi moi ket ban cho B, dang cho B tra loi.
    (A, B, 'accepted')  -> A va B da la ban be (chieu A -> B).
    (A, B, 'rejected')  -> B da tu choi loi moi cua A.

Khi B dong y ket ban, ngoai viec cap nhat dong (A, B) thanh 'accepted',
ta con tao/cap nhat them dong mirror (B, A, 'accepted') de viec kiem tra
"A va B co phai ban be khong" doi xung theo ca 2 chieu, khong phu thuoc
ai la nguoi gui loi moi truoc.
"""

from Code.backend.core.db_connection import db_cursor


def find_relationship(user_id: int, other_id: int) -> "dict | None":
    """Tra ve dong (user_id -> other_id) neu co, kem status."""
    with db_cursor() as cur:
        cur.execute(
            "SELECT id, status FROM contacts WHERE user_id = ? AND contact_id = ?",
            (user_id, other_id),
        )
        row = cur.fetchone()
    return dict(row) if row else None


def create_pending_request(from_id: int, to_id: int) -> None:
    with db_cursor() as cur:
        cur.execute(
            """INSERT INTO contacts (user_id, contact_id, status)
               VALUES (?, ?, 'pending')
               ON CONFLICT(user_id, contact_id)
               DO UPDATE SET status = 'pending', updated_at = datetime('now')""",
            (from_id, to_id),
        )


def accept_request(from_id: int, to_id: int) -> None:
    """B (to_id) dong y loi moi cua A (from_id) -> ket ban ca 2 chieu."""
    with db_cursor() as cur:
        cur.execute(
            "UPDATE contacts SET status = 'accepted' WHERE user_id = ? AND contact_id = ?",
            (from_id, to_id),
        )
        cur.execute(
            """INSERT INTO contacts (user_id, contact_id, status)
               VALUES (?, ?, 'accepted')
               ON CONFLICT(user_id, contact_id)
               DO UPDATE SET status = 'accepted', updated_at = datetime('now')""",
            (to_id, from_id),
        )


def reject_request(from_id: int, to_id: int) -> None:
    with db_cursor() as cur:
        cur.execute(
            "UPDATE contacts SET status = 'rejected' WHERE user_id = ? AND contact_id = ?",
            (from_id, to_id),
        )


def are_friends(user_id: int, other_id: int) -> bool:
    with db_cursor() as cur:
        cur.execute(
            """SELECT 1 FROM contacts
               WHERE user_id = ? AND contact_id = ? AND status = 'accepted'""",
            (user_id, other_id),
        )
        return cur.fetchone() is not None


def list_friend_usernames(user_id: int) -> list[str]:
    with db_cursor() as cur:
        cur.execute(
            """SELECT u.username FROM contacts c
               JOIN users u ON u.id = c.contact_id
               WHERE c.user_id = ? AND c.status = 'accepted'
               ORDER BY u.username""",
            (user_id,),
        )
        return [row["username"] for row in cur.fetchall()]


def list_incoming_pending_usernames(user_id: int) -> list[str]:
    """Nhung nguoi da gui loi moi ket ban CHO minh, dang cho minh tra loi."""
    with db_cursor() as cur:
        cur.execute(
            """SELECT u.username FROM contacts c
               JOIN users u ON u.id = c.user_id
               WHERE c.contact_id = ? AND c.status = 'pending'
               ORDER BY c.created_at""",
            (user_id,),
        )
        return [row["username"] for row in cur.fetchall()]